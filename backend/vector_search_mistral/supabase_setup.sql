-- Supabase setup script for vector search
-- Run this in the Supabase SQL editor to set up the required tables and functions

-- Enable vector extension if not already enabled
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Create pdf_documents table with vector embeddings support
CREATE TABLE IF NOT EXISTS pdf_documents (
  id TEXT PRIMARY KEY,
  embedding VECTOR(1024),  -- Mistral's embedding dimension
  content TEXT,            -- Document text content
  metadata JSONB,          -- Document metadata
  file_path TEXT,          -- Path to the original file
  chunk_id TEXT,           -- ID for the chunk within the document
  file_type TEXT           -- Type of file (pdf, etc.)
);

-- Create index on the embedding column for faster vector search
CREATE INDEX IF NOT EXISTS pdf_documents_embedding_idx ON pdf_documents USING ivfflat (embedding vector_cosine_ops);

-- Create indexes on common search fields for faster filtering
CREATE INDEX IF NOT EXISTS pdf_documents_file_path_idx ON pdf_documents (file_path);
CREATE INDEX IF NOT EXISTS pdf_documents_file_type_idx ON pdf_documents (file_type);

-- Create RPC function for vector similarity search
-- This function matches documents based on embedding similarity and optional filters
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(1024),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 5,
  filter_string TEXT DEFAULT NULL
)
RETURNS TABLE (
  id TEXT,
  content TEXT,
  metadata JSONB,
  file_path TEXT,
  chunk_id TEXT,
  file_type TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  IF filter_string IS NULL THEN
    -- No filter case
    RETURN QUERY
    SELECT
      pdf_documents.id,
      pdf_documents.content,
      pdf_documents.metadata,
      pdf_documents.file_path,
      pdf_documents.chunk_id,
      pdf_documents.file_type,
      1 - (pdf_documents.embedding <=> query_embedding) AS similarity
    FROM pdf_documents
    WHERE 1 - (pdf_documents.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
  ELSE
    -- With filter case - Use dynamic SQL to apply the filter
    RETURN QUERY EXECUTE
    format('
      SELECT
        pdf_documents.id,
        pdf_documents.content,
        pdf_documents.metadata,
        pdf_documents.file_path,
        pdf_documents.chunk_id,
        pdf_documents.file_type,
        1 - (pdf_documents.embedding <=> %L::vector) AS similarity
      FROM pdf_documents
      WHERE 
        1 - (pdf_documents.embedding <=> %L::vector) > %s
        AND %s
      ORDER BY similarity DESC
      LIMIT %s
    ', query_embedding, query_embedding, match_threshold, filter_string, match_count);
  END IF;
END;
$$;

-- Function to delete all documents from a specific file path
CREATE OR REPLACE FUNCTION delete_documents_by_path(file_path_to_delete TEXT)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  deleted_count INT;
BEGIN
  DELETE FROM pdf_documents
  WHERE file_path = file_path_to_delete
  RETURNING count(*) INTO deleted_count;
  
  RETURN deleted_count;
END;
$$;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
  total_documents BIGINT,
  unique_file_paths BIGINT,
  file_types JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    count(*)::BIGINT AS total_documents,
    count(DISTINCT file_path)::BIGINT AS unique_file_paths,
    (
      SELECT jsonb_object_agg(file_type, count)
      FROM (
        SELECT file_type, count(*)
        FROM pdf_documents
        GROUP BY file_type
      ) AS file_type_counts
    ) AS file_types
  FROM pdf_documents;
END;
$$; 
-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Function to search teams by embedding similarity
CREATE OR REPLACE FUNCTION match_teams(
  query_embedding vector,
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  name text,
  role text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    teams.id,
    teams.name,
    teams.role,
    1 - (teams.embedding <=> query_embedding) as similarity
  FROM teams
  WHERE 1 - (teams.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- Function to search sharded documents by embedding similarity
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector,
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  text_id uuid,
  document_id uuid,
  text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sharded_documents.text_id,
    sharded_documents.document_id,
    sharded_documents.text,
    1 - (sharded_documents.embedding <=> query_embedding) as similarity
  FROM sharded_documents
  WHERE 1 - (sharded_documents.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- Function to find most similar documents to a given document
CREATE OR REPLACE FUNCTION similar_documents(
  document_id uuid,
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  text_id uuid,
  document_id uuid,
  text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
DECLARE
  document_embedding vector;
BEGIN
  -- Get the embedding of the document chunks
  SELECT avg(embedding) INTO document_embedding
  FROM sharded_documents
  WHERE sharded_documents.document_id = $1;
  
  -- Return similar documents
  RETURN QUERY
  SELECT
    sharded_documents.text_id,
    sharded_documents.document_id,
    sharded_documents.text,
    1 - (sharded_documents.embedding <=> document_embedding) as similarity
  FROM sharded_documents
  WHERE 
    sharded_documents.document_id <> $1 AND
    1 - (sharded_documents.embedding <=> document_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$; 
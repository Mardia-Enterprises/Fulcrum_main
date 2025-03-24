-- Supabase setup script for Section F project parser
-- Run this in the Supabase SQL editor to set up the required tables and functions

-- Enable vector extension if not already enabled
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Create Section F projects table with vector embeddings
CREATE TABLE IF NOT EXISTS section_f_projects (
  id TEXT PRIMARY KEY,
  project_key TEXT NOT NULL,
  file_id TEXT,
  project_data JSONB NOT NULL,
  embedding VECTOR(1536) NOT NULL
);

-- Create index on project_key for faster lookup
CREATE INDEX IF NOT EXISTS section_f_projects_key_idx ON section_f_projects (project_key);

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_section_f_projects(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id TEXT,
  project_key TEXT,
  file_id TEXT,
  project_data JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    section_f_projects.id,
    section_f_projects.project_key,
    section_f_projects.file_id,
    section_f_projects.project_data,
    1 - (section_f_projects.embedding <=> query_embedding) AS similarity
  FROM section_f_projects
  WHERE 1 - (section_f_projects.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- Create function to search by project name (non-vector search)
CREATE OR REPLACE FUNCTION find_project_by_key(
  key_query TEXT
)
RETURNS TABLE (
  id TEXT,
  project_key TEXT,
  file_id TEXT,
  project_data JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    section_f_projects.id,
    section_f_projects.project_key,
    section_f_projects.file_id,
    section_f_projects.project_data
  FROM section_f_projects
  WHERE section_f_projects.project_key ILIKE '%' || key_query || '%'
  ORDER BY section_f_projects.project_key;
END;
$$;

-- Create function for full-text search inside project_data
CREATE OR REPLACE FUNCTION search_projects_text(search_query text)
RETURNS TABLE (
  id TEXT,
  project_key TEXT,
  file_id TEXT,
  project_data JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    section_f_projects.id,
    section_f_projects.project_key,
    section_f_projects.file_id,
    section_f_projects.project_data,
    0.8 AS similarity  -- Default similarity score for text matches
  FROM section_f_projects
  WHERE 
    to_tsvector('english', section_f_projects.project_data::text) @@ plainto_tsquery('english', search_query);
END;
$$;

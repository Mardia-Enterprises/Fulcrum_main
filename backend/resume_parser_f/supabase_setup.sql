-- This SQL script sets up the necessary tables and extensions for the resume parser
-- Run this in your Supabase SQL Editor (https://app.supabase.com/project/_/sql)

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Create projects table for Section F project data
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,           -- Unique project identifier
    title TEXT NOT NULL,           -- Project title for display
    project_data JSONB NOT NULL,   -- Complete project data as JSON
    embedding vector(1536),        -- OpenAI embedding (1536 dimensions)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ
);

-- Create an index for faster similarity searches
CREATE INDEX IF NOT EXISTS projects_embedding_idx ON projects USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_projects(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    title TEXT,
    project_data JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        projects.id,
        projects.title,
        projects.project_data,
        1 - (projects.embedding <=> query_embedding) AS similarity
    FROM projects
    WHERE 1 - (projects.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_projects_timestamp
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- (Optional) Row-level security policies
-- Uncomment and customize these if you want to use RLS

-- Enable row-level security
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users to select
-- CREATE POLICY select_projects ON projects
--     FOR SELECT TO authenticated
--     USING (true);

-- Create policy for authenticated users to insert
-- CREATE POLICY insert_projects ON projects
--     FOR INSERT TO authenticated
--     WITH CHECK (true);

-- Create policy for authenticated users to update their own projects
-- CREATE POLICY update_projects ON projects
--     FOR UPDATE TO authenticated
--     USING (true)
--     WITH CHECK (true);

-- Create policy for authenticated users to delete their own projects
-- CREATE POLICY delete_projects ON projects
--     FOR DELETE TO authenticated
--     USING (true);

-- Create an index on the project_owner field for faster filtering by owner
CREATE INDEX IF NOT EXISTS projects_owner_idx ON projects USING GIN ((project_data->'project_owner'));

-- Grant access to authenticated users (adjust as needed)
GRANT ALL ON TABLE projects TO service_role; 
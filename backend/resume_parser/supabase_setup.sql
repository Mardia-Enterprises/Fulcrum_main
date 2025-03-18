-- Supabase setup script for resume parser
-- Run this in the Supabase SQL editor to set up the required tables and functions

-- Enable vector extension if not already enabled
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Create employees table with vector embeddings support
CREATE TABLE IF NOT EXISTS employees (
  id TEXT PRIMARY KEY,
  employee_name TEXT NOT NULL,
  file_id TEXT,
  resume_data JSONB NOT NULL,
  embedding VECTOR(1536) NOT NULL
);

-- Create index on the employee_name for faster lookups
CREATE INDEX IF NOT EXISTS employees_name_idx ON employees (employee_name);

-- Create function for vector similarity search
CREATE OR REPLACE FUNCTION match_employees(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id TEXT,
  employee_name TEXT,
  file_id TEXT,
  resume_data JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    employees.id,
    employees.employee_name,
    employees.file_id,
    employees.resume_data,
    1 - (employees.embedding <=> query_embedding) AS similarity
  FROM employees
  WHERE 1 - (employees.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- Create a function to search by name (non-vector search)
CREATE OR REPLACE FUNCTION find_employee_by_name(
  name_query TEXT
)
RETURNS TABLE (
  id TEXT,
  employee_name TEXT,
  file_id TEXT,
  resume_data JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    employees.id,
    employees.employee_name,
    employees.file_id,
    employees.resume_data
  FROM employees
  WHERE employees.employee_name ILIKE '%' || name_query || '%'
  ORDER BY employees.employee_name;
END;
$$; 
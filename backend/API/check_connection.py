#!/usr/bin/env python
"""
Script to check the connection to Supabase and verify that the employees table exists
"""
import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Colors for console output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_color(text, color):
    print(f"{color}{text}{NC}")

# Load environment variables from the root .env file
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print_color(f"✓ Loaded environment variables from {env_path}", GREEN)
else:
    print_color(f"! Root .env file not found at {env_path}. Using system environment variables.", YELLOW)

# Check if required environment variables are set
required_vars = ["SUPABASE_PROJECT_URL", "SUPABASE_PRIVATE_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print_color(f"✗ The following required environment variables are not set: {', '.join(missing_vars)}", RED)
    print_color("Please set these variables in your .env file or system environment before running the API.", YELLOW)
    sys.exit(1)
else:
    print_color("✓ All required Supabase environment variables are set", GREEN)

# Try to connect to Supabase
try:
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    supabase = create_client(supabase_url, supabase_key)
    print_color("✓ Successfully connected to Supabase", GREEN)
    
    # Check if the employees table exists by fetching the first row
    try:
        result = supabase.table('employees').select('*').limit(1).execute()
        print_color("✓ Employees table exists", GREEN)
        
        # Check if there are any employees
        if result.data:
            employee_count = supabase.table('employees').select('*', count='exact').execute()
            print_color(f"✓ Found {len(employee_count.data)} employees in the database", GREEN)
            
            # Show the first employee as an example
            if result.data:
                print_color("\nExample employee:", GREEN)
                print(json.dumps(result.data[0], indent=2))
        else:
            print_color("! No employees found in the database", YELLOW)
            
        # Check if the vector extension and match_employees function exist
        try:
            # Try to perform a simple vector similarity search
            test_query = [0] * 1536  # Create a dummy vector of zeros
            vector_result = supabase.rpc(
                'match_employees',
                {
                    'query_embedding': test_query,
                    'match_threshold': 0.0,
                    'match_count': 1
                }
            ).execute()
            
            print_color("✓ Vector search functionality is working", GREEN)
        except Exception as e:
            print_color(f"✗ Vector search functionality is not working: {str(e)}", RED)
            print_color("\nMake sure to run the following SQL in your Supabase SQL Editor:", YELLOW)
            sql_setup = """
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create employees table with vector embeddings support
CREATE TABLE IF NOT EXISTS employees (
  id TEXT PRIMARY KEY,
  employee_name TEXT NOT NULL,
  file_id TEXT,
  resume_data JSONB NOT NULL,
  embedding VECTOR(1536) NOT NULL
);

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
"""
            print(sql_setup)
    
    except Exception as e:
        print_color(f"✗ Could not access employees table: {str(e)}", RED)
        print_color("Make sure the employees table exists in your Supabase database", YELLOW)
        
except Exception as e:
    print_color(f"✗ Failed to connect to Supabase: {str(e)}", RED)
    print_color("Check your SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY values", YELLOW)
    sys.exit(1)

print_color("\nConnection check complete", GREEN) 
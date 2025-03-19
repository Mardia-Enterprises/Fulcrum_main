#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}   Employee Resume API Deployment      ${NC}"
echo -e "${GREEN}=======================================${NC}"

# Change to the root directory
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

# Function to check for environment variables
check_env_var() {
  if [ -z "${!1}" ]; then
    echo -e "${RED}Error: $1 is not set in the .env file${NC}"
    return 1
  else
    echo -e "${GREEN}✓ $1 is set${NC}"
    return 0
  fi
}

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}Warning: .env file not found in root directory.${NC}"
  echo -e "${YELLOW}Creating a template .env file. Please update it with your API keys.${NC}"
  cat > .env << EOF
# OpenAI API key for embeddings
OPENAI_API_KEY=your_openai_api_key

# Supabase credentials
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
EOF
  echo -e "${YELLOW}Please edit the .env file with your actual API keys before proceeding.${NC}"
  exit 1
fi

# Check for virtual environment
if [ ! -d "backend/.venv" ]; then
  echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
  cd backend
  python3 -m venv .venv
  cd "$ROOT_DIR"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source backend/.venv/bin/activate || { echo -e "${RED}Failed to activate virtual environment${NC}"; exit 1; }

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r backend/API/requirements.txt || { echo -e "${RED}Failed to install dependencies${NC}"; exit 1; }

# Load environment variables
source .env

# Check for required environment variables
echo -e "${GREEN}Checking environment variables...${NC}"
env_error=0
check_env_var "OPENAI_API_KEY" || env_error=1
check_env_var "SUPABASE_PROJECT_URL" || env_error=1
check_env_var "SUPABASE_PRIVATE_API_KEY" || env_error=1

if [ $env_error -eq 1 ]; then
  echo -e "${RED}Please update the .env file with the missing API keys and run the script again.${NC}"
  exit 1
fi

# Setup Supabase database
echo -e "${GREEN}Setting up Supabase database...${NC}"
echo -e "${YELLOW}Note: You need to manually run the following SQL in your Supabase SQL Editor:${NC}"
echo ""
echo "-- Enable vector extension"
echo "CREATE EXTENSION IF NOT EXISTS vector;"
echo ""
echo "-- Create employees table with vector embeddings support"
echo "CREATE TABLE IF NOT EXISTS employees ("
echo "  id TEXT PRIMARY KEY,"
echo "  employee_name TEXT NOT NULL,"
echo "  file_id TEXT,"
echo "  resume_data JSONB NOT NULL,"
echo "  embedding VECTOR(1536) NOT NULL"
echo ");"
echo ""
echo "-- Create function for vector similarity search"
echo "CREATE OR REPLACE FUNCTION match_employees("
echo "  query_embedding VECTOR(1536),"
echo "  match_threshold FLOAT,"
echo "  match_count INT"
echo ")"
echo "RETURNS TABLE ("
echo "  id TEXT,"
echo "  employee_name TEXT,"
echo "  file_id TEXT,"
echo "  resume_data JSONB,"
echo "  similarity FLOAT"
echo ")"
echo "LANGUAGE plpgsql"
echo "AS \$\$"
echo "BEGIN"
echo "  RETURN QUERY"
echo "  SELECT"
echo "    employees.id,"
echo "    employees.employee_name,"
echo "    employees.file_id,"
echo "    employees.resume_data,"
echo "    1 - (employees.embedding <=> query_embedding) AS similarity"
echo "  FROM employees"
echo "  WHERE 1 - (employees.embedding <=> query_embedding) > match_threshold"
echo "  ORDER BY similarity DESC"
echo "  LIMIT match_count;"
echo "END;"
echo "\$\$;"
echo ""

# Done
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}   API Deployment Complete!            ${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "You can start the API with:"
echo -e "${YELLOW}cd backend/API${NC}"
echo -e "${YELLOW}python run_api.py${NC}"
echo ""
echo -e "API will be available at: ${GREEN}http://localhost:8000${NC}"
echo -e "API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo "" 
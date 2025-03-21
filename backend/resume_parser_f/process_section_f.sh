#!/bin/bash

# Script to process Section F PDFs and upload them to Supabase

# Set text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}=== Section F PDF Processor ===${NC}"

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate the virtual environment if it exists
if [ -d "../.venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source ../.venv/bin/activate
elif [ -d "../../.venv" ]; then
    echo -e "${BLUE}Activating virtual environment from project root...${NC}"
    source ../../.venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Using system Python.${NC}"
    echo -e "${YELLOW}It's recommended to create a virtual environment.${NC}"
fi

# Check if we have required environment variables
function check_env_var {
    local var_name=$1
    if [ -z "${!var_name}" ]; then
        # Try to load from .env file
        if [ -f "../../.env" ]; then
            source <(grep -v '^#' ../../.env | sed -E 's/(.*)=(.*)$/export \1="\2"/g')
        fi
        
        # Check again
        if [ -z "${!var_name}" ]; then
            echo -e "${RED}Error: $var_name environment variable not set${NC}"
            echo -e "${YELLOW}Please set this in your .env file${NC}"
            return 1
        fi
    fi
    return 0
}

# Check required environment variables
echo -e "${BLUE}Checking environment variables...${NC}"
check_env_var "MISTRAL_API_KEY" || exit 1
check_env_var "OPENAI_API_KEY" || exit 1
check_env_var "SUPABASE_PROJECT_URL" || exit 1
check_env_var "SUPABASE_PRIVATE_API_KEY" || exit 1

echo -e "${GREEN}✓ Environment variables found${NC}"

# Create required directories
echo -e "${BLUE}Creating required directories...${NC}"
mkdir -p output
mkdir -p debug

# Define PDF directory
if [ -n "$1" ]; then
    PDF_DIR="$1"
else
    # Default to "Section F Resumes" directory in parent
    PDF_DIR="../Section F Resumes"
    
    # If that doesn't exist, try root level
    if [ ! -d "$PDF_DIR" ]; then
        PDF_DIR="../../Section F Resumes"
    fi
fi

# Check if the PDF directory exists
if [ ! -d "$PDF_DIR" ]; then
    echo -e "${RED}Error: PDF directory not found at $PDF_DIR${NC}"
    echo -e "${YELLOW}Please provide a valid directory as the first argument${NC}"
    echo -e "${YELLOW}Example: $0 /path/to/pdfs${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using PDF directory: $PDF_DIR${NC}"

# Count the number of PDFs
NUM_PDFS=$(find "$PDF_DIR" -name "*.pdf" | wc -l)
if [ "$NUM_PDFS" -eq 0 ]; then
    echo -e "${RED}Error: No PDF files found in $PDF_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Found $NUM_PDFS PDF files to process${NC}"

# Process PDFs with the Python script
echo -e "${BLUE}${BOLD}Processing Section F PDFs...${NC}"
python3 process_projects.py --pdf-dir "$PDF_DIR"

# Check if processing was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Processing failed${NC}"
    exit 1
fi

echo -e "${GREEN}${BOLD}✓ Processing completed successfully${NC}"

# List the projects in Supabase
echo -e "${BLUE}${BOLD}Verifying projects in Supabase...${NC}"
echo -e "${BLUE}The following projects should now be in the Supabase database:${NC}"

# Use Python to query Supabase and display projects
python3 -c "
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
script_dir = Path.cwd()
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root .env file
load_dotenv(root_dir / '.env')

# Initialize Supabase client
try:
    from supabase import create_client
    supabase_url = os.getenv('SUPABASE_PROJECT_URL')
    supabase_key = os.getenv('SUPABASE_PRIVATE_API_KEY')
    
    if not supabase_url or not supabase_key:
        print('\033[91mError: Supabase credentials not found\033[0m')
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Query all projects
    result = supabase.table('projects').select('id, title, project_data->>project_owner').execute()
    
    if not result.data:
        print('\033[93mNo projects found in Supabase\033[0m')
        sys.exit(1)
    
    print(f'\033[92mFound {len(result.data)} projects in Supabase:\033[0m')
    for project in result.data:
        print(f'  - {project.get(\"title\")} (Owner: {project.get(\"project_owner\", \"Unknown\")})')
    
except Exception as e:
    print(f'\033[91mError querying Supabase: {str(e)}\033[0m')
    sys.exit(1)
"

# Deactivate virtual environment if we activated it
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo -e "${BLUE}Virtual environment deactivated${NC}"
fi

echo -e "${GREEN}${BOLD}✓ All tasks completed successfully${NC}"
echo -e "${BLUE}Check the resume_parser.log file for detailed logs${NC}" 
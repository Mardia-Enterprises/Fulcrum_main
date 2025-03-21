#!/bin/bash

# Shell script to process Section F PDFs
# This script calls the resume_parser_f/execute_processor.sh script

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

# Define root directory (one level up from backend)
ROOT_DIR="$( cd .. && pwd )"
ENV_FILE="${ROOT_DIR}/.env"

# Check if .env file exists in the root directory
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found in root directory: ${ENV_FILE}${NC}"
    echo -e "${YELLOW}Creating a template .env file in the root directory...${NC}"
    cat > "$ENV_FILE" << EOF
# Environment variables for the Fulcrum backend
# This file should be placed in the root directory and not committed to version control

# Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Supabase credentials
SUPABASE_PROJECT_URL=your_supabase_url_here
SUPABASE_PRIVATE_API_KEY=your_supabase_key_here

# API settings
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=True
EOF
    echo -e "${YELLOW}Please edit the .env file in the root directory with your actual API keys${NC}"
    exit 1
fi

echo -e "${GREEN}Using .env file from root directory: ${ENV_FILE}${NC}"

# Check if the resume_parser_f directory exists
if [ ! -d "resume_parser_f" ]; then
    echo -e "${RED}Error: resume_parser_f directory not found${NC}"
    exit 1
fi

# Check if the execute_processor.sh script exists
if [ ! -f "resume_parser_f/execute_processor.sh" ]; then
    echo -e "${RED}Error: execute_processor.sh not found in resume_parser_f directory${NC}"
    exit 1
fi

# Check if the Section F Resumes directory exists
if [ ! -d "Section F Resumes" ]; then
    echo -e "${YELLOW}Warning: Section F Resumes directory not found${NC}"
    echo -e "${YELLOW}Creating Section F Resumes directory...${NC}"
    mkdir -p "Section F Resumes"
fi

# Check if there are PDF files in the Section F Resumes directory
PDF_COUNT=$(find "Section F Resumes" -name "*.pdf" | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No PDF files found in Section F Resumes directory${NC}"
    echo -e "${YELLOW}Please add PDF files to the Section F Resumes directory before running this script${NC}"
    exit 1
fi

echo -e "${GREEN}Found $PDF_COUNT PDF files to process${NC}"

# Pass the root directory .env file path to the execute_processor.sh script
echo -e "${BLUE}${BOLD}Running PDF processor...${NC}"
ENV_FILE_PATH="$ENV_FILE" ./resume_parser_f/execute_processor.sh

# Check the exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Processing completed successfully${NC}"
elif [ $EXIT_CODE -eq 2 ]; then
    echo -e "${YELLOW}${BOLD}⚠ Processing completed with some failures${NC}"
    echo -e "${YELLOW}Check the logs for details${NC}"
else
    echo -e "${RED}${BOLD}✗ Processing failed${NC}"
    echo -e "${RED}Check the logs for details${NC}"
    exit 1
fi

echo -e "${GREEN}${BOLD}✓ Done${NC}" 
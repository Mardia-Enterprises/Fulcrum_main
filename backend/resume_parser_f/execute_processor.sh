#!/bin/bash

# Shell script to execute the direct PDF processor script
# This script ensures the proper Python environment is activated

# Set text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}=== Section F PDF Direct Processor ===${NC}"

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Get the root directory (two levels up from the script directory)
ROOT_DIR="$( cd ../.. && pwd )"

# Use the .env file path passed from the parent script or default to root directory
if [ -n "$ENV_FILE_PATH" ]; then
    ENV_FILE="$ENV_FILE_PATH"
else
    ENV_FILE="${ROOT_DIR}/.env"
fi

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at ${ENV_FILE}${NC}"
    echo -e "${RED}Please ensure your .env file is in the root directory${NC}"
    exit 1
fi

echo -e "${GREEN}Using .env file: ${ENV_FILE}${NC}"

# Export the .env file path as an environment variable for Python scripts
export DOTENV_PATH="$ENV_FILE"

# Activate the virtual environment if it exists
if [ -d "../.venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source ../.venv/bin/activate
elif [ -d "../../.venv" ]; then
    echo -e "${BLUE}Activating virtual environment from project root...${NC}"
    source ../../.venv/bin/activate
elif [ -d "../venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source ../venv/bin/activate
elif [ -d "../../venv" ]; then
    echo -e "${BLUE}Activating virtual environment from project root...${NC}"
    source ../../venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Using system Python.${NC}"
    echo -e "${YELLOW}It's recommended to create a virtual environment.${NC}"
fi

# Check if direct_pdf_processor.py exists
if [ ! -f "direct_pdf_processor.py" ]; then
    echo -e "${RED}Error: direct_pdf_processor.py not found${NC}"
    echo -e "${RED}Make sure you are running this script from the resume_parser_f directory${NC}"
    exit 1
fi

# Check if the Section F Resumes directory exists
RESUME_DIR="../Section F Resumes"
if [ ! -d "$RESUME_DIR" ]; then
    echo -e "${RED}Error: Section F Resumes directory not found at $RESUME_DIR${NC}"
    exit 1
fi

# Check if there are PDF files in the Section F Resumes directory
PDF_COUNT=$(find "$RESUME_DIR" -name "*.pdf" | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No PDF files found in $RESUME_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Found $PDF_COUNT PDF files to process${NC}"

# Run the direct PDF processor script with the .env file path
echo -e "${BLUE}${BOLD}Running direct PDF processor...${NC}"
python3 -c "import os; os.environ['DOTENV_PATH']='$ENV_FILE'" direct_pdf_processor.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✓ Processing completed successfully${NC}"
elif [ $? -eq 2 ]; then
    echo -e "${YELLOW}${BOLD}⚠ Processing completed with some failures${NC}"
else
    echo -e "${RED}${BOLD}✗ Processing failed${NC}"
    exit 1
fi

# Deactivate virtual environment if we activated it
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
    echo -e "${BLUE}Virtual environment deactivated${NC}"
fi

echo -e "${BLUE}Check the direct_pdf_processor.log file for detailed logs${NC}"
echo -e "${GREEN}${BOLD}✓ Done${NC}" 
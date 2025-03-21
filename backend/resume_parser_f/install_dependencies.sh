#!/bin/bash

# Script to install missing dependencies for resume_parser_f

# Set text colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Installing missing dependencies for Section F Parser ===${NC}"

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Find and activate the virtual environment
if [ -d "../.venv" ]; then
    echo -e "${GREEN}Activating virtual environment in backend/.venv${NC}"
    source ../.venv/bin/activate
elif [ -d "../../venv" ]; then
    echo -e "${GREEN}Activating virtual environment in project root venv${NC}"
    source ../../venv/bin/activate
else
    echo -e "${YELLOW}No existing virtual environment found. Creating one...${NC}"
    python3 -m venv ../.venv
    source ../.venv/bin/activate
    echo -e "${GREEN}Created and activated new virtual environment${NC}"
fi

# Install the required packages
echo -e "${BLUE}Installing mistralai package (version 0.4.2)...${NC}"
pip uninstall -y mistralai
pip install mistralai==0.4.2
echo -e "${YELLOW}Note: Using mistralai version 0.4.2 specifically for compatibility${NC}"
echo -e "${YELLOW}The code includes a compatibility layer for this version${NC}"

# Install other potentially missing packages
echo -e "${BLUE}Installing other required packages...${NC}"
pip install python-dotenv openai supabase pdfplumber

echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
echo -e "${YELLOW}Now you can run process_section_f.sh to process PDFs${NC}" 
#!/bin/bash

# Script to install all required dependencies for the resume parser

# Set text colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}=== Installing Dependencies ===${NC}"

# Change to backend directory if script is run from elsewhere
cd "$(dirname "$0")"
echo -e "${BLUE}Working directory: $(pwd)${NC}"

# Activate the existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment from .venv${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}Virtual environment not found. Creating new one...${NC}"
    python -m venv .venv
    source .venv/bin/activate
fi

# Check if the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo -e "${BLUE}Using Python: $(which python)${NC}"
echo -e "${BLUE}Python version: $(python --version)${NC}"

# Install core dependencies
echo -e "${BLUE}Installing core dependencies...${NC}"
pip install -U pip wheel setuptools

# Install Mistral AI client
echo -e "${BLUE}Installing Mistral AI client...${NC}"
pip install --upgrade mistralai

# Install OpenAI
echo -e "${BLUE}Installing OpenAI client...${NC}"
pip install --upgrade openai

# Install Supabase and pgvector
echo -e "${BLUE}Installing Supabase client...${NC}"
pip install supabase pgvector

# Install other dependencies
echo -e "${BLUE}Installing other dependencies...${NC}"
pip install python-dotenv requests

# Check if we have a requirements.txt file and install from it
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Installing packages from requirements.txt...${NC}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}No requirements.txt found. Skipping.${NC}"
fi

# Check all important dependencies
echo -e "${BLUE}${BOLD}Checking dependencies...${NC}"
python -c "
import sys
dependencies = {
    'mistralai': 'Mistral AI client',
    'openai': 'OpenAI client',
    'supabase': 'Supabase client',
    'dotenv': 'Environment variables manager',
    'pgvector': 'Vector extension for Postgres'
}

print('Installed packages:')
for package, description in dependencies.items():
    try:
        __import__(package)
        print(f'\033[92m✓ {package}: {description}\033[0m')
    except ImportError:
        print(f'\033[91m✗ {package}: Not installed\033[0m')
        if package == 'dotenv':
            print('  Try: pip install python-dotenv')
        else:
            print(f'  Try: pip install {package}')
"

# Report success
echo -e "${GREEN}${BOLD}✓ Dependencies installation complete!${NC}"
echo -e "${BLUE}You may now run the backend with:${NC}"
echo -e "${GREEN}./process_projects.sh${NC}"

# Deactivate virtual environment
deactivate
echo -e "${BLUE}Virtual environment deactivated${NC}" 
#!/bin/bash

# Set colors for terminal output
BLUE="\033[1;34m"
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== Project Profiles API Server ===${NC}"

# Check if we're in the correct directory
if [[ ! -f "main.py" && ! -f "run_api.py" ]]; then
    echo -e "${RED}Error: Not in the API_projects directory${NC}"
    echo -e "${YELLOW}Please run this script from the API_projects directory${NC}"
    exit 1
fi

# Check for virtual environment
VENV_PATH="../.venv"
if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "${YELLOW}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
fi

# Activate the virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install dependencies if needed
echo -e "${BLUE}Checking dependencies...${NC}"
pip install -r requirements.txt

# Set environment variables
export API_PORT=8001

# Run the API
echo -e "${GREEN}Starting Project Profiles API on port 8001...${NC}"
python run_api.py

# Deactivate virtual environment on exit
deactivate 
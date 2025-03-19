#!/bin/bash

# Deployment script for PDF Vector Search Engine
# This script sets up the environment and shows how to use the system

# Set color codes for output formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}       PDF Vector Search Engine Deployment         ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Change to the root directory
cd "$(dirname "$0")/../.."
ROOT_DIR=$(pwd)

# Step 1: Check if backend/.venv exists
echo -e "\n${YELLOW}Step 1: Checking Python virtual environment...${NC}"
if [ -d "backend/.venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found at backend/.venv${NC}"
else
    echo -e "${RED}✗ Virtual environment not found at backend/.venv${NC}"
    echo -e "${YELLOW}Creating new virtual environment...${NC}"
    cd backend
    python3 -m venv .venv
    cd ..
    echo -e "${GREEN}✓ Virtual environment created at backend/.venv${NC}"
fi

# Step 2: Activate virtual environment and install dependencies
echo -e "\n${YELLOW}Step 2: Activating virtual environment and installing dependencies...${NC}"
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/vector_search_mistral/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Download NLTK data
echo -e "\n${YELLOW}Step 3: Downloading NLTK data...${NC}"
# Try the simple approach first
python -m nltk.downloader punkt || {
    # If that fails, try with SSL verification disabled
    echo -e "${YELLOW}Simple download failed, trying with SSL verification disabled...${NC}"
    python -c "import nltk, ssl; ssl._create_default_https_context = ssl._create_unverified_context; nltk.download('punkt')" || {
        echo -e "${RED}✗ NLTK data download failed${NC}"
        echo -e "${YELLOW}The system will use alternative text processing methods.${NC}"
        echo -e "${YELLOW}You can manually download punkt from:${NC}"
        echo -e "${YELLOW}https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip${NC}"
        echo -e "${YELLOW}and extract to ~/.nltk_data/tokenizers/punkt${NC}"
    }
}
echo -e "${GREEN}✓ Proceeding with deployment${NC}"

# Step 4: Check for root .env file
echo -e "\n${YELLOW}Step 4: Checking for root .env file...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Root .env file found at ${ROOT_DIR}/.env${NC}"
else
    echo -e "${RED}✗ Root .env file not found at ${ROOT_DIR}/.env${NC}"
    echo -e "${YELLOW}Creating a template .env file...${NC}"
    cat > .env << EOL
# Required environment variables
MISTRAL_API_KEY=your_mistral_api_key_here
SUPABASE_PROJECT_URL=your_supabase_url_here
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Required for RAG features

# Optional configuration
SUPABASE_TABLE_NAME=pdf_documents
MISTRAL_MODEL=mistral-embed
OPENAI_MODEL=gpt-3.5-turbo
EOL
    echo -e "${GREEN}✓ Template .env file created at ${ROOT_DIR}/.env${NC}"
    echo -e "${YELLOW}Please update the .env file with your actual API keys and configuration.${NC}"
fi

# Step 5: Check environment variables
echo -e "\n${YELLOW}Step 5: Checking environment variables...${NC}"
cd backend
source .venv/bin/activate
python -m vector_search_mistral.check_env
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Some environment variables are missing in the root .env file${NC}"
    echo -e "${YELLOW}Please update the .env file in the project root directory.${NC}"
else
    echo -e "${GREEN}✓ All required environment variables are set in the root .env file${NC}"
fi

# Step 6: Remind about Supabase setup
echo -e "\n${YELLOW}Step 6: Supabase setup reminder...${NC}"
echo -e "${BLUE}Don't forget to set up your Supabase database:${NC}"
echo -e "1. Log in to your Supabase dashboard"
echo -e "2. Go to the SQL Editor"
echo -e "3. Run the SQL script from backend/vector_search_mistral/supabase_setup.sql"
echo -e "${YELLOW}This will create the necessary tables and functions for vector search.${NC}"

# Step 7: Remind about PDF directory
echo -e "\n${YELLOW}Step 7: PDF directory setup...${NC}"
if [ ! -d "backend/pdf_data/raw-files" ]; then
    mkdir -p backend/pdf_data/raw-files
    echo -e "${GREEN}✓ Created PDF directory at backend/pdf_data/raw-files${NC}"
else
    echo -e "${GREEN}✓ PDF directory already exists at backend/pdf_data/raw-files${NC}"
fi
echo -e "${BLUE}Please place your PDF files in the backend/pdf_data/raw-files directory.${NC}"

# Step 8: Usage examples
echo -e "\n${YELLOW}Step 8: Usage examples${NC}"
echo -e "\n${BLUE}To process PDF documents:${NC}"
echo -e "cd backend && source .venv/bin/activate"
echo -e "python -m vector_search_mistral.run process --pdf-dir pdf_data/raw-files"
echo -e "\n${BLUE}To search PDF documents:${NC}"
echo -e "cd backend && source .venv/bin/activate"
echo -e "python -m vector_search_mistral.run search \"your search query\""
echo -e "\n${BLUE}To search with RAG enhancement:${NC}"
echo -e "cd backend && source .venv/bin/activate"
echo -e "python -m vector_search_mistral.run search \"your search query\" --rag"

# Final message
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}       PDF Vector Search Engine is Ready!          ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "\nThank you for deploying the PDF Vector Search Engine!"
echo -e "Remember to use only the .env file in the project root directory for environment variables." 
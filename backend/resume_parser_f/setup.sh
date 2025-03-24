#!/bin/bash

# Resume Parser Setup Script
echo "Setting up Section F Resume Parser..."

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists, otherwise create it
if [ -d "../.venv" ]; then
    echo "Activating existing virtual environment..."
    source ../.venv/bin/activate
else
    echo "Creating new virtual environment..."
    cd ..
    python -m venv .venv
    source .venv/bin/activate
    cd resume_parser
fi

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists in the root directory
if [ -f "../../.env" ]; then
    echo "Environment file found in root directory."
    
    # Check for required API keys
    if grep -q "MISTRAL_API_KEY" ../../.env && \
       grep -q "OPENAI_API_KEY" ../../.env && \
       grep -q "SUPABASE_PROJECT_URL" ../../.env && \
       grep -q "SUPABASE_PRIVATE_API_KEY" ../../.env; then
        echo "All required API keys found in .env file."
    else
        echo "WARNING: Some required API keys are missing from .env file."
        echo "Please ensure the following variables are set:"
        echo "- MISTRAL_API_KEY"
        echo "- OPENAI_API_KEY"
        echo "- SUPABASE_PROJECT_URL"
        echo "- SUPABASE_PRIVATE_API_KEY"
    fi
else
    echo "WARNING: No .env file found in root directory."
    echo "Please create one with the required API keys."
fi

# Create PDF directory
echo "Creating Section F Resumes directory..."
mkdir -p "../Section F Resumes"
echo "Directory created. Please place your SF 330 Section E PDFs in 'backend/Section E Resumes/'."

# Supabase setup reminder
echo ""
echo "==== Supabase Setup ===="
echo "Remember to set up the Supabase database before running the parser."
echo "Navigate to your Supabase project's SQL Editor and run the supabase_setup.sql script."
echo "This script will create the necessary tables and functions for vector search."
echo ""

# NLTK data download
echo "Downloading NLTK data if needed..."
python -c "import nltk; nltk.download('punkt')"

echo ""
echo "Setup complete! You can now run the resume parser with:"
echo "cd backend && source .venv/bin/activate && python -m resume_parser.dataparser" 
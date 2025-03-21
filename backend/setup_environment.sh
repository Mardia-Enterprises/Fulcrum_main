#!/bin/bash
# Script to set up the environment for the backend

# Change to backend directory
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

# Check if .venv exists
if [ -d ".venv" ]; then
    echo "Virtual environment .venv already exists."
    
    # Ask before upgrading
    read -p "Do you want to upgrade the existing environment? (y/n): " upgrade_choice
    if [ "$upgrade_choice" = "y" ]; then
        echo "Activating existing virtual environment..."
        source .venv/bin/activate
        
        # Install/upgrade requirements
        echo "Installing/upgrading requirements..."
        pip install -U fastapi uvicorn supabase openai python-dotenv mistralai
        
        echo "Environment upgraded successfully."
    else
        echo "Skipping environment upgrade."
    fi
else
    echo "Creating new virtual environment in .venv..."
    python3 -m venv .venv
    
    echo "Activating virtual environment..."
    source .venv/bin/activate
    
    # Update pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    echo "Installing requirements..."
    pip install fastapi uvicorn supabase openai python-dotenv mistralai
    
    echo "Virtual environment created and dependencies installed."
fi

# Check for .env file
if [ -f "../.env" ]; then
    echo ".env file exists in parent directory."
else
    echo "Creating template .env file in parent directory..."
    cat > "../.env" << EOL
# API Keys
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key

# Supabase Configuration
SUPABASE_PROJECT_URL=your_supabase_project_url
SUPABASE_PRIVATE_API_KEY=your_supabase_api_key

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8001
EOL
    echo "Template .env file created. Please edit it with your actual API keys."
fi

# Test dependencies
echo "Testing key dependencies..."
python -c "
try:
    import fastapi
    import uvicorn
    import supabase
    import openai
    from dotenv import load_dotenv
    from mistralai import Mistral
    print('All dependencies imported successfully!')
except ImportError as e:
    print(f'Error importing dependency: {e}')
"

# Create directory for PDF files if it doesn't exist
if [ ! -d "Section F Resumes" ]; then
    echo "Creating directory for Section F resumes..."
    mkdir -p "Section F Resumes"
    echo "Please place your PDF files in the 'Section F Resumes' directory."
fi

echo ""
echo "===================================================================="
echo "Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys"
echo "2. Place your PDF files in the 'Section F Resumes' directory"
echo "3. Run the database setup SQL in Supabase (see resume_parser_f/supabase_setup.sql)"
echo "4. Process PDFs: ./process_projects.sh"
echo "5. Run the API: ./run_api.sh"
echo ""
echo "For troubleshooting:"
echo "- Test Supabase connection: ./debug_supabase.py"
echo "- Test Mistral API: ./debug_mistral.py"
echo "===================================================================="

# Deactivate virtual environment
deactivate 
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the project root directory
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Virtual environment directory
VENV_DIR="$PROJECT_ROOT/backend/.venv"

# Print header
echo "======================================"
echo "  PDF Vector Search Setup Script"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version)
echo "✅ Found $PYTHON_VERSION"

# Check if virtualenv is installed, install if not
if ! python3 -m pip show virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    python3 -m pip install virtualenv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m virtualenv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        exit 1
    fi
    echo "✅ Virtual environment created."
else
    echo "✅ Using existing virtual environment at $VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if activation was successful
if [ $? -ne 0 ] || [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment."
    exit 1
fi
echo "✅ Virtual environment activated."

# Install requirements
echo "Installing requirements..."
python -m pip install -r "$SCRIPT_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements."
    exit 1
fi
echo "✅ Requirements installed successfully."

# Download NLTK data
echo "Downloading NLTK data..."
python "$SCRIPT_DIR/download_nltk_data.py"
if [ $? -ne 0 ]; then
    echo "⚠️ Warning: NLTK data download had issues, but we'll continue with setup."
else
    echo "✅ NLTK data downloaded successfully."
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/pdf-search"
chmod +x "$SCRIPT_DIR/run.py"
chmod +x "$SCRIPT_DIR/check_env.py"
chmod +x "$SCRIPT_DIR/example_usage.py"
chmod +x "$SCRIPT_DIR/test_setup.py"
if [ $? -ne 0 ]; then
    echo "❌ Failed to make scripts executable."
    exit 1
fi
echo "✅ Made scripts executable."

# Create .env file if it doesn't exist
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file from example..."
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create .env file."
    else
        echo "✅ Created .env file. Please edit it to add your API keys."
        echo "   File location: $ENV_FILE"
    fi
else
    echo "✅ .env file already exists at $ENV_FILE"
    
    # Check if OPENAI_API_KEY is in .env file
    if ! grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
        echo "⚠️ No OPENAI_API_KEY found in .env file."
        echo "   If you want to use the RAG features, please add your OpenAI API key:"
        echo "   OPENAI_API_KEY=your_openai_api_key"
    else
        echo "✅ OPENAI_API_KEY found in .env file."
    fi
fi

# Create PDF directories
mkdir -p "$PROJECT_ROOT/pdf_data/raw-files"
mkdir -p "$PROJECT_ROOT/pdf_data/example-pdfs"

# Run test setup to verify everything is working
echo ""
echo "Running setup verification..."
python "$SCRIPT_DIR/test_setup.py"

echo ""
echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "To use the PDF vector search system:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source $VENV_DIR/bin/activate"
echo ""
echo "2. Run the processing command:"
echo "   $SCRIPT_DIR/pdf-search process --pdf-dir pdf_data/raw-files"
echo ""
echo "3. Run a search query:"
echo "   $SCRIPT_DIR/pdf-search search \"your search query\""
echo ""
echo "4. Run a search with OpenAI RAG processing:"
echo "   $SCRIPT_DIR/pdf-search search \"your search query\" --rag --rag-mode explain"
echo ""
echo "For more information, run:"
echo "   $SCRIPT_DIR/pdf-search"
echo "" 
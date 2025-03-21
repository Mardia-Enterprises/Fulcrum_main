#!/bin/bash

# Script to run the API server using the existing .venv

# Change to backend directory
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

# Activate the existing virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment from .venv"
    source .venv/bin/activate
else
    echo "Error: Virtual environment .venv not found in backend directory"
    exit 1
fi

# Check if the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run the API server
echo "Starting API server..."
cd API_projects
python run_api.py

# Deactivate virtual environment (this will only run if the API server is stopped)
deactivate
echo "API server stopped. Virtual environment deactivated." 
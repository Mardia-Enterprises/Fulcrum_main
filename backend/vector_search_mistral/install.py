#!/usr/bin/env python3
"""
Production Installation Script for PDF Vector Search Engine
-------------------------------------------------------------------------------
This script automates the installation process for the PDF Vector Search Engine
in a production environment. It performs the following tasks:
1. Checks for required dependencies
2. Sets up environment variables
3. Downloads necessary resources
4. Verifies the installation
"""

import os
import sys
import logging
import subprocess
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("install")

def run_command(command, description=None):
    """Run a shell command and log the output."""
    if description:
        logger.info(description)
    
    logger.debug(f"Running command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        if result.stdout.strip():
            logger.debug(result.stdout.strip())
        return True, result.stdout
    else:
        logger.error(f"Command failed with error code {result.returncode}")
        if result.stderr.strip():
            logger.error(result.stderr.strip())
        return False, result.stderr

def check_python_version():
    """Check if Python version is compatible."""
    logger.info("Checking Python version...")
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required.")
        return False
    logger.info(f"Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected.")
    return True

def install_dependencies(requirements_file):
    """Install required Python packages."""
    logger.info(f"Installing dependencies from {requirements_file}...")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    # Install dependencies
    success, _ = run_command(f"pip install -r {requirements_file}", "Installing Python packages...")
    return success

def setup_env_file(env_example_file, env_file, overwrite=False):
    """Create .env file from .env.example if it doesn't exist."""
    logger.info("Setting up environment file...")
    
    # Check if example env file exists
    if not os.path.exists(env_example_file):
        logger.error(f"Environment example file not found: {env_example_file}")
        return False
    
    # Check if env file already exists
    if os.path.exists(env_file) and not overwrite:
        logger.info(f"Environment file already exists: {env_file}")
        logger.info("To overwrite, run with --overwrite-env")
        return True
    
    # Copy example env file to env file
    try:
        with open(env_example_file, 'r') as example_file:
            example_content = example_file.read()
        
        with open(env_file, 'w') as env_file_obj:
            env_file_obj.write(example_content)
        
        logger.info(f"Created environment file: {env_file}")
        logger.info("IMPORTANT: Edit the .env file to set your API keys and other configuration.")
        return True
    except Exception as e:
        logger.error(f"Error creating environment file: {str(e)}")
        return False

def download_nltk_data():
    """Download required NLTK data."""
    logger.info("Downloading NLTK data...")
    
    # Import the NLTK downloader script
    try:
        script_dir = Path(__file__).resolve().parent
        nltk_script = script_dir / "download_nltk_data.py"
        
        if not nltk_script.exists():
            logger.error(f"NLTK download script not found: {nltk_script}")
            return False
        
        success, _ = run_command(f"python {nltk_script}", "Downloading NLTK data...")
        return success
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {str(e)}")
        return False

def verify_installation():
    """Verify the installation by running a simple test."""
    logger.info("Verifying installation...")
    
    # Run a simple test to verify installation
    try:
        script_dir = Path(__file__).resolve().parent
        pdf_search_script = script_dir / "pdf-search"
        
        if not pdf_search_script.exists():
            logger.error(f"PDF search script not found: {pdf_search_script}")
            return False
        
        success, _ = run_command(f"python {pdf_search_script} --help", "Testing PDF search command...")
        return success
    except Exception as e:
        logger.error(f"Error verifying installation: {str(e)}")
        return False

def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install PDF Vector Search Engine")
    parser.add_argument("--overwrite-env", action="store_true", help="Overwrite existing .env file")
    parser.add_argument("--requirements", default=None, help="Path to requirements.txt file")
    parser.add_argument("--no-nltk", action="store_true", help="Skip NLTK data download")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting PDF Vector Search Engine installation...")
    
    # Get script directory
    script_dir = Path(__file__).resolve().parent
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Determine requirements file path
    requirements_file = args.requirements
    if not requirements_file:
        requirements_file = script_dir / "requirements.txt"
    
    # Install dependencies
    if not install_dependencies(requirements_file):
        logger.error("Failed to install dependencies.")
        return 1
    
    # Set up environment file
    env_example_file = script_dir / ".env.example"
    env_file = script_dir / ".env"
    if not setup_env_file(env_example_file, env_file, args.overwrite_env):
        logger.error("Failed to set up environment file.")
        return 1
    
    # Download NLTK data
    if not args.no_nltk:
        if not download_nltk_data():
            logger.warning("Failed to download NLTK data. Some functionality may be limited.")
    
    # Verify installation
    if not verify_installation():
        logger.error("Installation verification failed.")
        logger.error("Please check your environment setup and try again.")
        return 1
    
    logger.info("Installation completed successfully!")
    logger.info("IMPORTANT: Make sure to set your API keys in the .env file.")
    logger.info("To use the PDF Vector Search Engine, run: python -m backend.vector_search_mistral [command]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
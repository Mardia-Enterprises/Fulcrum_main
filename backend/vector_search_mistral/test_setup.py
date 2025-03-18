#!/usr/bin/env python3
"""
Test script to verify that the PDF search engine is set up correctly.
This script checks imports, environment variables, and basic functionality.
"""

import os
import sys
import importlib
import importlib.metadata
import subprocess
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Define color constants for fallback without colorama
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Try to use colorama if available
try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
    USE_COLOR = True
    # Map colorama colors to our colors
    COLOR_GREEN = Fore.GREEN
    COLOR_YELLOW = Fore.YELLOW
    COLOR_RED = Fore.RED
    COLOR_CYAN = Fore.CYAN
    COLOR_RESET = Style.RESET_ALL
    COLOR_BOLD = Style.BRIGHT
except ImportError:
    USE_COLOR = False
    # Use ANSI escape codes as fallback
    COLOR_GREEN = GREEN
    COLOR_YELLOW = YELLOW
    COLOR_RED = RED
    COLOR_CYAN = CYAN
    COLOR_RESET = RESET
    COLOR_BOLD = BOLD

# Configure logging
logging.basicConfig(level=logging.ERROR, format="%(message)s")
logger = logging.getLogger(__name__)

def colorize(text, color_code, bold=False):
    """Apply color to text with fallback for systems without colorama"""
    if USE_COLOR:
        bold_code = COLOR_BOLD if bold else ""
        return f"{bold_code}{color_code}{text}{COLOR_RESET}"
    else:
        bold_code = BOLD if bold else ""
        return f"{bold_code}{color_code}{text}{RESET}"

def success(message):
    """Format a success message"""
    prefix = colorize("✓", COLOR_GREEN, bold=True)
    return f"{prefix} {message}"

def warning(message):
    """Format a warning message"""
    prefix = colorize("!", COLOR_YELLOW, bold=True)
    return f"{prefix} {message}"

def error(message):
    """Format an error message"""
    prefix = colorize("✗", COLOR_RED, bold=True)
    return f"{prefix} {message}"

def heading(message):
    """Format a heading"""
    if USE_COLOR:
        return f"\n{colorize(message, COLOR_CYAN, bold=True)}\n{colorize('='*50, COLOR_CYAN)}\n"
    else:
        return f"\n{colorize(message, COLOR_CYAN, bold=True)}\n{'='*50}\n"

def is_in_virtualenv():
    """Check if we're running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_virtualenv_path():
    """Get the path to the active virtual environment."""
    if is_in_virtualenv():
        return sys.prefix
    return None

def check_python_version():
    """Check if the Python version is supported."""
    major, minor, patch = sys.version_info[:3]
    version_str = f"{major}.{minor}.{patch}"
    
    if major >= 3 and minor >= 8:
        print(success(f"Python version {version_str} is supported"))
        return True
    else:
        print(error(f"Python version {version_str} is not supported - need Python 3.8+"))
        return False

def check_virtualenv():
    """Check if running in a virtual environment."""
    if is_in_virtualenv():
        venv_path = get_virtualenv_path()
        print(success(f"Running in virtual environment: {venv_path}"))
        return True
    else:
        print(error("Not running in a virtual environment"))
        return False

def is_package_installed(package_name):
    """Check if a package is installed using importlib.metadata."""
    try:
        # Try to get the version using importlib.metadata
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        try:
            # Try to import the package as a fallback
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

def get_package_version(package_name):
    """Get the version of an installed package."""
    try:
        version = importlib.metadata.version(package_name)
        return version
    except (importlib.metadata.PackageNotFoundError, Exception):
        try:
            # Try to import and get version attribute
            module = importlib.import_module(package_name)
            if hasattr(module, '__version__'):
                return module.__version__
            if hasattr(module, 'VERSION'):
                return module.VERSION
            return "unknown"
        except (ImportError, AttributeError):
            return None

def check_required_packages():
    """Check if required packages are installed."""
    required_packages = [
        "mistralai",
        "pinecone",
        "python-dotenv",
        "nltk",
        "pathlib"
    ]
    
    optional_packages = [
        "openai"  # Optional for RAG features
    ]
    
    all_installed = True
    
    # Check required packages
    for package in required_packages:
        if is_package_installed(package):
            version = get_package_version(package)
            version_str = f"(version: {version})" if version else ""
            print(success(f"{package} is installed {version_str}"))
        else:
            print(error(f"{package} is not installed"))
            all_installed = False
    
    # Check optional packages
    for package in optional_packages:
        if is_package_installed(package):
            version = get_package_version(package)
            version_str = f"(version: {version})" if version else ""
            print(success(f"{package} is installed {version_str}"))
        else:
            print(warning(f"{package} is not installed - needed for RAG features"))
    
    return all_installed

def check_env_variables():
    """Check if required environment variables are set."""
    required_vars = ["MISTRAL_API_KEY", "PINECONE_API_KEY", "PINECONE_REGION"]
    optional_vars = ["OPENAI_API_KEY"]  # Optional for RAG features
    
    try:
        from dotenv import load_dotenv
        
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(success(f"Loaded environment variables from {env_path}"))
        else:
            print(warning("No .env file found"))
    except ImportError:
        print(warning("python-dotenv not installed, skipping .env loading"))
    
    all_set = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Hide most of the API key for security
            masked_value = value[:4] + "..." if len(value) > 4 else "***"
            print(success(f"{var} is set: {masked_value}"))
        else:
            print(error(f"{var} is not set"))
            all_set = False
    
    # Check optional variables
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            # Hide most of the API key for security
            masked_value = value[:4] + "..." if len(value) > 4 else "***"
            print(success(f"{var} is set: {masked_value}"))
        else:
            print(warning(f"{var} is not set - needed for RAG features"))
    
    return all_set

def check_nltk_data():
    """Check if NLTK data is downloaded."""
    try:
        import nltk
        
        try:
            nltk.data.find('tokenizers/punkt')
            print(success("NLTK punkt tokenizer is downloaded"))
            return True
        except LookupError:
            print(error("NLTK punkt tokenizer is not downloaded"))
            return False
    except ImportError:
        print(error("NLTK is not installed"))
        return False

def check_openai_integration():
    """Check if OpenAI integration is available."""
    try:
        from openai import OpenAI
        
        # Check if API key is set
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            print(success("OpenAI package is installed and API key is set"))
            # Don't actually create a client or make an API call to avoid spending credits
            return True
        else:
            print(warning("OpenAI package is installed but API key is not set"))
            return False
    except ImportError:
        print(warning("OpenAI package is not installed - RAG features will not be available"))
        return False
    except Exception as e:
        print(warning(f"Error checking OpenAI integration: {str(e)}"))
        return False

def check_module_imports():
    """Check if all required modules can be imported."""
    # First try to import pinecone directly
    try:
        import pinecone
        print(success("Successfully imported pinecone package"))
    except ImportError as e:
        print(error(f"Failed to import pinecone: {str(e)}"))
        return False
    
    # Now check all the other modules
    modules_to_check = [
        "backend.vector_search_mistral.text_preprocessor",
        "backend.vector_search_mistral.pinecone_indexer",
        "backend.vector_search_mistral.embeddings_generator",
        "backend.vector_search_mistral.pdf_processor",
        "backend.vector_search_mistral.query_engine",
        "backend.vector_search_mistral.main"
    ]
    
    # Check optional RAG module
    optional_modules = [
        "backend.vector_search_mistral.openai_processor"
    ]
    
    all_imported = True
    for module_name in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(success(f"Successfully imported {module_name}"))
        except Exception as e:
            print(error(f"Failed to import {module_name}: {str(e)}"))
            all_imported = False
    
    # Check optional modules
    for module_name in optional_modules:
        try:
            importlib.import_module(module_name)
            print(success(f"Successfully imported {module_name}"))
        except Exception as e:
            print(warning(f"Failed to import {module_name}: {str(e)} - RAG features may not be available"))
    
    return all_imported

def main():
    """Run all checks and print a summary."""
    print(heading("PDF Vector Search System - Setup Verification"))
    
    print(heading("Checking Python Version"))
    python_check = check_python_version()
    
    print(heading("Checking Virtual Environment"))
    venv_check = check_virtualenv()
    
    print(heading("Checking Required Packages"))
    packages_check = check_required_packages()
    
    print(heading("Checking Environment Variables"))
    env_check = check_env_variables()
    
    print(heading("Checking NLTK Data"))
    nltk_check = check_nltk_data()
    
    print(heading("Checking OpenAI Integration (Optional)"))
    openai_check = check_openai_integration()
    
    print(heading("Checking Module Imports"))
    imports_check = check_module_imports()
    
    # Print summary
    print(heading("Summary"))
    print(f"Python Version: {colorize('PASS', COLOR_GREEN) if python_check else colorize('FAIL', COLOR_RED)}")
    print(f"Virtual Environment: {colorize('PASS', COLOR_GREEN) if venv_check else colorize('FAIL', COLOR_RED)}")
    print(f"Dependencies: {colorize('PASS', COLOR_GREEN) if packages_check else colorize('FAIL', COLOR_RED)}")
    print(f"Environment Variables: {colorize('PASS', COLOR_GREEN) if env_check else colorize('FAIL', COLOR_RED)}")
    print(f"NLTK Data: {colorize('PASS', COLOR_GREEN) if nltk_check else colorize('FAIL', COLOR_RED)}")
    print(f"Module Imports: {colorize('PASS', COLOR_GREEN) if imports_check else colorize('FAIL', COLOR_RED)}")
    print(f"OpenAI Integration: {colorize('PASS', COLOR_GREEN) if openai_check else colorize('OPTIONAL', COLOR_YELLOW)}")
    
    all_passed = python_check and venv_check and packages_check and env_check and nltk_check and imports_check
    
    print()
    if all_passed:
        status = "All checks passed!"
        if not openai_check:
            status += " OpenAI integration is optional and not fully configured."
        print(colorize(f"Overall Status: {status} The system is ready to use.", COLOR_GREEN, bold=True))
        return 0
    else:
        print(colorize("Overall Status: Some checks failed. Please fix the issues before using the system.", COLOR_YELLOW, bold=True))
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
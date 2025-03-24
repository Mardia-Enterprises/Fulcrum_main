#!/usr/bin/env python3
"""
Check for required environment variables.

This script checks if all the environment variables required by the
PDF Vector Search Engine are set. It's useful for troubleshooting 
environment configuration issues.
"""

import os
import sys
from typing import Tuple, List, Optional, Any

def load_environment() -> bool:
    """
    Load environment variables from the root .env file.
    
    Returns:
        bool: True if environment variables were loaded successfully
    """
    try:
        from dotenv import load_dotenv
        
        # Get the path to the root .env file
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        env_path = os.path.join(root_dir, ".env")
        
        # Load environment variables
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"Loaded environment variables from {env_path}")
            return True
        else:
            print(f"Root .env file not found at {env_path}. Using system environment variables.")
            return False
    except ImportError:
        print("python-dotenv not installed. Using system environment variables.")
        return False

def is_mistral_available() -> bool:
    """
    Check if the Mistral AI package is available.
    
    Returns:
        bool: True if the package is available
    """
    try:
        import mistralai
        # Also check for the client module which is required
        from mistralai.client import MistralClient
        from mistralai.models.embeddings import EmbeddingResponse
        return True
    except ImportError:
        return False

def check_required_variables() -> Tuple[bool, List[Tuple[str, str]]]:
    """
    Check if all required environment variables are set.
    
    Returns:
        tuple: (success, list of missing variables with descriptions)
    """
    # Load environment variables from the root .env file
    load_environment()
    
    # Define required variables with descriptions
    required_vars = [
        ("MISTRAL_API_KEY", "Required for OCR text extraction and embedding generation."),
        ("SUPABASE_PROJECT_URL", "Required for Supabase configuration."),
        ("SUPABASE_PRIVATE_API_KEY", "Required for Supabase configuration."),
    ]
    
    # If Mistral is not available, we need OpenAI for embeddings
    if not is_mistral_available():
        required_vars.append(("OPENAI_API_KEY", "Required for embeddings if Mistral is not available."))
    
    missing_vars = []
    
    # Check each required variable
    for var_name, description in required_vars:
        if not os.environ.get(var_name):
            missing_vars.append((var_name, description))
    
    # Check optional variables and set defaults if needed
    if not os.environ.get("SUPABASE_TABLE_NAME"):
        os.environ["SUPABASE_TABLE_NAME"] = "pdf_documents"
        print(f"Info: Using default SUPABASE_TABLE_NAME = 'pdf_documents'")
    
    # Return results
    if missing_vars:
        return False, missing_vars
    else:
        return True, []

def main() -> bool:
    """
    Main function that checks environment variables and prints the results.
    
    Returns:
        bool: True if all required variables are set
    """
    success, missing_vars = check_required_variables()
    
    if not success:
        print("\n⚠️  Missing environment variables:")
        for var_name, description in missing_vars:
            print(f"  - {var_name}: {description}")
        
        print("\nPlease set these environment variables in the root .env file.")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 
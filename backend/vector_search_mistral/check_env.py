#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

def main():
    """Check if all required environment variables are set."""
    # Load environment variables from .env file
    dotenv_path = find_dotenv()
    if dotenv_path:
        print(f"Using .env file from: {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        print("Warning: No .env file found. Using environment variables already set.")
    
    # List of required environment variables
    required_vars = [
        ("MISTRAL_API_KEY", "Required for OCR text extraction and embedding generation."),
        ("PINECONE_API_KEY", "Required for vector storage and retrieval."),
        ("PINECONE_ENVIRONMENT", "Required for Pinecone configuration.")
    ]
    
    missing_vars = []
    
    # Check each required environment variable
    for var_name, description in required_vars:
        if not os.environ.get(var_name):
            missing_vars.append((var_name, description))
    
    # Print results
    if missing_vars:
        print("\n⚠️  Missing environment variables:")
        for var_name, description in missing_vars:
            print(f"  - {var_name}: {description}")
        
        print("\nPlease set these environment variables in a .env file or in your shell.")
        print("Example .env file content:")
        print("--------------------------")
        for var_name, _ in required_vars:
            print(f"{var_name}=your_{var_name.lower()}")
        
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def find_dotenv():
    """Find the .env file by checking multiple locations."""
    # Check current directory
    if Path(".env").exists():
        return Path(".env").resolve()
    
    # Check script directory
    script_dir = Path(__file__).parent.resolve()
    if (script_dir / ".env").exists():
        return (script_dir / ".env").resolve()
    
    # Check project root
    project_root = script_dir.parent.parent
    if (project_root / ".env").exists():
        return (project_root / ".env").resolve()
    
    return None

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 
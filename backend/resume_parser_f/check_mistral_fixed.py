#!/usr/bin/env python3
"""
Script to check if the fixed Mistral AI client can be properly imported and used.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mistral_fixed_check.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root directory
load_dotenv(root_dir / ".env")
logger.info(f"Loading environment variables from: {root_dir / '.env'}")

def check_mistral_client():
    """Check if the Mistral AI client can be initialized and used"""
    logger.info("Checking if Mistral AI client (v0.4.2) can be initialized...")
    
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        logger.error("MISTRAL_API_KEY not found in environment variables")
        return False
    
    try:
        # Import the mistralai package
        import mistralai
        logger.info("✓ Successfully imported mistralai package")
        
        # Import the MistralClient class
        from mistralai.client import MistralClient
        logger.info("✓ Successfully imported MistralClient")
        
        # Initialize the client
        client = MistralClient(api_key=mistral_api_key)
        logger.info("✓ Successfully initialized MistralClient")
        
        # Try a simple completion request
        logger.info("Testing Mistral API with a simple completion request...")
        response = client.chat(
            model="mistral-tiny",
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            max_tokens=10
        )
        logger.info(f"✓ Successfully received response from Mistral AI")
        logger.info(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        logger.error(f"Error with Mistral AI client: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("=== Mistral AI Client Check (Fixed Version) ===")
    
    # Print Python information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    
    # Check if Mistral AI client can be initialized and used
    if not check_mistral_client():
        logger.error("Failed to initialize or use Mistral AI client")
        return 1
    
    logger.info("✓ All checks passed successfully")
    logger.info("You should now be able to run process_section_f.sh without errors")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
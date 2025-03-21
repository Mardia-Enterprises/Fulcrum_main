#!/usr/bin/env python3
"""
Script to check if the Mistral AI client can be properly imported and initialized.
This will help diagnose the issue with the process_section_f.sh script.
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
        logging.FileHandler("mistral_check.log"),
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

def check_mistral_import():
    """Check if the Mistral AI client can be imported"""
    logger.info("Checking if mistralai can be imported...")
    
    try:
        import mistralai
        logger.info(f"✓ Successfully imported mistralai version {mistralai.__version__}")
        
        try:
            from mistralai.client import MistralClient
            logger.info("✓ Successfully imported MistralClient")
            return True
        except ImportError as e:
            logger.error(f"Error importing MistralClient: {str(e)}")
            return False
    except ImportError as e:
        logger.error(f"Error importing mistralai package: {str(e)}")
        logger.info("Trying to install mistralai...")
        
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai"])
            logger.info("✓ Successfully installed mistralai")
            
            # Try importing again
            import mistralai
            from mistralai.client import MistralClient
            logger.info(f"✓ Successfully imported mistralai version {mistralai.__version__}")
            return True
        except Exception as e:
            logger.error(f"Failed to install mistralai: {str(e)}")
            return False

def check_mistral_client():
    """Check if the Mistral AI client can be initialized and used"""
    logger.info("Checking if Mistral AI client can be initialized...")
    
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        logger.error("MISTRAL_API_KEY not found in environment variables")
        return False
    
    try:
        from mistralai.client import MistralClient
        client = MistralClient(api_key=mistral_api_key)
        logger.info("✓ Successfully initialized MistralClient")
        
        # Try a simple completion request
        try:
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
            logger.error(f"Error calling Mistral API: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error initializing MistralClient: {str(e)}")
        return False

def print_python_path():
    """Print the Python path to help diagnose import issues"""
    logger.info("Python path:")
    for path in sys.path:
        logger.info(f"  - {path}")

def main():
    """Main function"""
    logger.info("=== Mistral AI Client Check ===")
    
    # Print Python information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    
    # Print Python path
    print_python_path()
    
    # Check if mistralai can be imported
    if not check_mistral_import():
        logger.error("Failed to import mistralai")
        return 1
    
    # Check if Mistral AI client can be initialized and used
    if not check_mistral_client():
        logger.error("Failed to initialize or use Mistral AI client")
        return 1
    
    logger.info("✓ All checks passed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
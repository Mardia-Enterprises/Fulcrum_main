#!/usr/bin/env python3
"""
Script to fix the Mistral AI client version issue.
This will install the correct version (0.4.2) of the mistralai package.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mistral_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def install_correct_version():
    """Install the correct version of the mistralai package"""
    logger.info("Installing mistralai version 0.4.2...")
    
    try:
        # First uninstall any existing version
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "mistralai"])
        logger.info("Uninstalled existing mistralai package")
        
        # Install the correct version
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mistralai==0.4.2"])
        logger.info("✓ Successfully installed mistralai version 0.4.2")
        
        # Verify the installation
        try:
            import mistralai
            from mistralai.client import MistralClient
            logger.info(f"✓ Successfully imported mistralai version {mistralai.__version__}")
            
            # Try to initialize the client
            logger.info("Testing client initialization...")
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if mistral_api_key:
                client = MistralClient(api_key=mistral_api_key)
                logger.info("✓ Successfully initialized MistralClient")
            else:
                logger.warning("MISTRAL_API_KEY not found in environment variables")
                logger.warning("Skipping client initialization test")
                
            return True
        except ImportError as e:
            logger.error(f"Error importing mistralai after installation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error testing mistralai client: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error installing mistralai: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info("=== Mistral AI Package Fix ===")
    
    # Print Python information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    
    # Install the correct version
    if not install_correct_version():
        logger.error("Failed to install the correct version of mistralai")
        return 1
    
    logger.info("✓ Fix completed successfully")
    logger.info("You should now be able to run process_section_f.sh without errors")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
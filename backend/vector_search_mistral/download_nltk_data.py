#!/usr/bin/env python
"""
NLTK Data Downloader for Vector Search
-------------------------------------------------------------------------------
This script downloads the required NLTK data packages for the PDF Vector Search 
Engine. It downloads the 'punkt' tokenizer, which is used for sentence splitting
during text preprocessing.

This script is intended to be run once during deployment or first-time setup.
"""

import os
import sys
import logging
import nltk
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("nltk_downloader")

def download_nltk_data(data_dir: str = None, packages: list = None):
    """
    Download the required NLTK data packages.
    
    Args:
        data_dir: Directory to store the NLTK data (defaults to nltk_data in user home)
        packages: List of NLTK packages to download (defaults to ['punkt'])
    
    Returns:
        True if the download was successful, False otherwise
    """
    try:
        # Default packages to download
        if packages is None:
            packages = ['punkt']
        
        # Set the NLTK data directory
        if data_dir:
            nltk.data.path.append(data_dir)
            os.environ['NLTK_DATA'] = data_dir
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Using custom NLTK data directory: {data_dir}")
        else:
            # Use the default NLTK data directory
            data_dir = str(Path.home() / 'nltk_data')
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Using default NLTK data directory: {data_dir}")
        
        # Download the required packages
        success = True
        for package in packages:
            try:
                logger.info(f"Downloading NLTK package: {package}")
                nltk.download(package, quiet=False, raise_on_error=True)
                logger.info(f"Successfully downloaded NLTK package: {package}")
            except Exception as e:
                logger.error(f"Error downloading NLTK package '{package}': {str(e)}")
                success = False
        
        return success
    
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {str(e)}")
        return False

if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Download NLTK data")
    parser.add_argument("--data-dir", help="Directory to store NLTK data")
    parser.add_argument("--packages", nargs='+', default=['punkt'],
                        help="NLTK packages to download (default: punkt)")
    args = parser.parse_args()
    
    # Download the required NLTK data
    success = download_nltk_data(args.data_dir, args.packages)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 
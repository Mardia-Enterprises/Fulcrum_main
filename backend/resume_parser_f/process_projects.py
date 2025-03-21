#!/usr/bin/env python3
"""
Script to process Section F PDFs and upload to Supabase.
This script combines dataparser.py and datauploader.py into a single workflow.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - \033[1;33m%(levelname)s\033[0m - %(message)s',
    handlers=[
        logging.FileHandler("resume_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

def check_environment() -> bool:
    """
    Check that all required environment variables are set.
    
    Returns:
        True if all environment variables are set, False otherwise
    """
    logger.info("Checking environment variables...")
    
    # Check for Mistral API key
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        logger.error("\033[91mError: MISTRAL_API_KEY not found in .env file\033[0m")
        logger.error("Please add your Mistral API key to the .env file in the root directory")
        return False
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("\033[91mError: OPENAI_API_KEY not found in .env file\033[0m")
        logger.error("Please add your OpenAI API key to the .env file in the root directory")
        return False
    
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    if not supabase_url or not supabase_key:
        logger.error("\033[91mError: Supabase credentials not found in .env file\033[0m")
        logger.error("Please add your Supabase URL and API key to the .env file in the root directory")
        return False
    
    logger.info("\033[92m✓ All required environment variables are set\033[0m")
    return True

def import_dependencies() -> bool:
    """
    Import all required dependencies.
    
    Returns:
        True if all dependencies are imported successfully, False otherwise
    """
    logger.info("Importing dependencies...")
    
    try:
        # Import specific libraries that are required
        from mistralai.client import MistralClient
        from openai import OpenAI
        from supabase import create_client
        
        # Import functions from our modules
        from dataparser import process_pdf_directory, extract_structured_data_with_mistral
        from datauploader import process_json_files, upsert_project_in_supabase
        
        logger.info("\033[92m✓ All dependencies imported successfully\033[0m")
        return True
    except ImportError as e:
        logger.error(f"\033[91mError importing dependencies: {str(e)}\033[0m")
        logger.error("Please install required dependencies with 'pip install -r requirements.txt'")
        return False
    except Exception as e:
        logger.error(f"\033[91mUnexpected error importing dependencies: {str(e)}\033[0m")
        return False

def process_pdfs_to_supabase(
    pdf_dir: Union[str, Path], 
    limit: Optional[int] = None,
    skip_upload: bool = False
) -> bool:
    """
    Process PDFs and upload to Supabase.
    
    Args:
        pdf_dir: Directory containing PDF files
        limit: Maximum number of PDFs to process (None for all)
        skip_upload: If True, skip the upload to Supabase step
        
    Returns:
        True if processing was successful, False otherwise
    """
    # Import the required modules
    try:
        from dataparser import process_pdf_directory
        from datauploader import process_json_files
    except ImportError:
        logger.error("\033[91mError importing required modules\033[0m")
        sys.path.append(str(script_dir))
        try:
            from dataparser import process_pdf_directory
            from datauploader import process_json_files
        except ImportError:
            logger.error("\033[91mFailed to import required modules\033[0m")
            return False
    
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"\033[91mError: PDF directory not found: {pdf_dir}\033[0m")
        return False
    
    logger.info(f"\n\033[1;36m===== Processing PDFs in: {pdf_dir} =====\033[0m")
    
    # Step 1: Process PDFs to extract structured data
    logger.info("Step 1: Extracting structured data from PDFs...")
    extracted_data = process_pdf_directory(pdf_dir, limit)
    
    if not extracted_data:
        logger.error("\033[91mNo data extracted from PDFs\033[0m")
        return False
    
    logger.info(f"\033[92m✓ Successfully extracted data from {len(extracted_data)} PDFs\033[0m")
    
    # If skip_upload is True, stop here
    if skip_upload:
        logger.info("Skipping upload to Supabase as requested")
        return True
    
    # Step 2: Process JSON files to upload to Supabase
    logger.info("\nStep 2: Uploading extracted data to Supabase...")
    output_dir = script_dir / "output"
    success_count = process_json_files(output_dir, limit)
    
    if success_count == 0:
        logger.error("\033[91mFailed to upload any data to Supabase\033[0m")
        return False
    
    logger.info(f"\033[92m✓ Successfully uploaded {success_count} projects to Supabase\033[0m")
    return True

def direct_process_sample() -> bool:
    """
    Process a sample project directly from example data.
    Useful for testing the upload process without PDFs.
    
    Returns:
        True if the process was successful, False otherwise
    """
    logger.info("\n\033[1;36m===== Processing Sample Project =====\033[0m")
    
    # Import the required module
    try:
        from datauploader import upsert_project_in_supabase
    except ImportError:
        logger.error("\033[91mError importing required module\033[0m")
        sys.path.append(str(script_dir))
        try:
            from datauploader import upsert_project_in_supabase
        except ImportError:
            logger.error("\033[91mFailed to import required module\033[0m")
            return False
    
    # Sample project data based on the provided JSON structure
    sample_project = {
        "project_owner": "USACE Fort Worth District",
        "year_completed": {
            "construction": None,
            "professional_services": 2019
        },
        "point_of_contact": "555-555-5555",
        "brief_description": "The Granger Lake Management staff required a new administrative office facility due to the presence of black mold. The project included the remediation and demolition of the existing 5,890 SF lake management facility and the design of a new facility with increased water pressure, a large conference room, and a grandiose lobby area. The project schedule was cut by two months to facilitate the obligation of Recreational Funds before the end of the 2019 Fiscal Year. The new facility is one story and was designed for approximately 4,856 SF in gross area, and includes offices, a conference room, site lighting, parking, and a government vehicle and equipment compound fencing design. The building is oriented with the long sides facing north/south and the narrow sides facing east/west, with windows featuring double paned glass and Low-E coating for maximum energy efficiency. The Prime completed all of the mechanical design for this facility, which complied with various codes and included heating, ventilating, air conditioning, refrigeration, energy, piping and plumbing systems.",
        "title_and_location": "Granger Lake Management Office Building Design, Granger, TX",
        "firms_from_section_c": [
            {
                "role": "Prime: Architecture, Civil, Structural, and MEP",
                "firm_name": "MSMM Engineering",
                "firm_location": "New Orleans, LA"
            },
            {
                "role": "Sub: Civil, Structural, and ITR",
                "firm_name": "Huitt-Zollars, Inc.",
                "firm_location": "Fort Worth, TX"
            }
        ],
        "point_of_contact_name": "John Doe, Project Manager"
    }
    
    # Generate a project ID
    project_id = "sample_granger_lake_office"
    title = sample_project["title_and_location"]
    
    # Upload to Supabase
    logger.info(f"Uploading sample project: {title}")
    success = upsert_project_in_supabase(project_id, title, sample_project)
    
    if success:
        logger.info(f"\033[92m✓ Successfully uploaded sample project to Supabase\033[0m")
        return True
    else:
        logger.error("\033[91mFailed to upload sample project to Supabase\033[0m")
        return False

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Process Section F PDFs and upload to Supabase")
    parser.add_argument("--pdf-dir", default=None, help="Directory containing PDF files")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of PDFs to process")
    parser.add_argument("--skip-upload", action="store_true", help="Skip uploading to Supabase")
    parser.add_argument("--sample", action="store_true", help="Process a sample project instead of PDFs")
    return parser.parse_args()

def main():
    """Main function to run the script"""
    logger.info("\033[1;36m===== Section F PDF Processor =====\033[0m")
    
    # Parse command line arguments
    args = parse_args()
    
    # Check environment
    if not check_environment():
        logger.error("\033[91mEnvironment check failed. Please fix the issues and try again.\033[0m")
        return 1
    
    # Import dependencies
    if not import_dependencies():
        logger.error("\033[91mDependency check failed. Please fix the issues and try again.\033[0m")
        return 1
    
    # Process sample or PDFs
    if args.sample:
        # Process sample project
        success = direct_process_sample()
    else:
        # Process PDFs
        if args.pdf_dir:
            pdf_dir = args.pdf_dir
        else:
            # Default to "Section F Resumes" in the parent directory
            pdf_dir = script_dir.parent / "Section F Resumes"
        
        success = process_pdfs_to_supabase(pdf_dir, args.limit, args.skip_upload)
    
    if success:
        logger.info("\033[92m✓ Processing completed successfully\033[0m")
        return 0
    else:
        logger.error("\033[91mProcessing failed\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
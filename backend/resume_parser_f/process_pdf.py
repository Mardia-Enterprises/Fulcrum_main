#!/usr/bin/env python3
"""
Script to directly process a Section F PDF from the Section F Resumes folder.
This script uses dataparser.py and datauploader.py to process and upload the data.
"""

import os
import sys
import logging
from pathlib import Path
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

# Load environment variables from root .env file only
load_dotenv(root_dir / ".env")
logger.info(f"Loading environment variables from: {root_dir / '.env'}")

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
        logger.error(f"Please add your Mistral API key to the .env file in the root directory: {root_dir / '.env'}")
        return False
    
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("\033[91mError: OPENAI_API_KEY not found in .env file\033[0m")
        logger.error(f"Please add your OpenAI API key to the .env file in the root directory: {root_dir / '.env'}")
        return False
    
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    if not supabase_url or not supabase_key:
        logger.error("\033[91mError: Supabase credentials not found in .env file\033[0m")
        logger.error(f"Please add your Supabase URL and API key to the .env file in the root directory: {root_dir / '.env'}")
        return False
    
    logger.info("\033[92m✓ All required environment variables are set\033[0m")
    return True

def process_actual_pdf():
    """
    Process a specific PDF from Section F Resumes folder
    """
    # Import the processing modules
    try:
        from dataparser import process_pdf_file
        from datauploader import upsert_project_in_supabase, project_to_text, generate_embedding
    except ImportError as e:
        logger.error(f"\033[91mError importing required modules: {e}\033[0m")
        sys.exit(1)
    
    # Define the PDF path - using the one in Section F Resumes
    pdf_dir = script_dir.parent / "Section F Resumes"
    pdf_path = pdf_dir / "SectionF.pdf"
    
    if not pdf_path.exists():
        logger.error(f"\033[91mError: PDF file not found: {pdf_path}\033[0m")
        sys.exit(1)
    
    logger.info(f"\n\033[1;36m===== Processing PDF: {pdf_path} =====\033[0m")
    
    # Step 1: Process the PDF to extract structured data
    logger.info("Step 1: Extracting structured data from PDF...")
    project_data = process_pdf_file(pdf_path)
    
    if not project_data:
        logger.error("\033[91mNo data extracted from PDF\033[0m")
        sys.exit(1)
    
    logger.info(f"\033[92m✓ Successfully extracted data from PDF\033[0m")
    
    # Step 2: Generate a project ID and upload to Supabase
    title = project_data.get("title_and_location", "Unknown Project")
    # Create a clean ID from the title
    clean_title = title.lower().replace(" ", "_").replace(",", "").replace(".", "")
    project_id = f"proj_{clean_title[:30]}"
    
    # Upload to Supabase
    logger.info("\nStep 2: Uploading extracted data to Supabase...")
    success = upsert_project_in_supabase(project_id, title, project_data)
    
    if not success:
        logger.error("\033[91mFailed to upload data to Supabase\033[0m")
        sys.exit(1)
    
    logger.info(f"\033[92m✓ Successfully uploaded project to Supabase\033[0m")
    return project_data

if __name__ == "__main__":
    # Check environment
    if not check_environment():
        logger.error("\033[91mEnvironment check failed. Please fix the issues and try again.\033[0m")
        sys.exit(1)
    
    try:
        # Process the PDF
        project_data = process_actual_pdf()
        
        # Print a summary of the extracted data
        print("\n\033[1;36m===== Extracted Project Data =====\033[0m")
        print(f"Title: {project_data.get('title_and_location', 'Unknown')}")
        print(f"Owner: {project_data.get('project_owner', 'Unknown')}")
        
        # Check for firms
        firms = project_data.get('firms_from_section_c', [])
        if firms:
            print(f"Firms involved: {len(firms)}")
            for firm in firms:
                print(f"  - {firm.get('firm_name', 'Unknown')} ({firm.get('role', 'Unknown')})")
        
        logger.info("\033[92m✓ Processing completed successfully\033[0m")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\033[91mError during processing: {str(e)}\033[0m")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 
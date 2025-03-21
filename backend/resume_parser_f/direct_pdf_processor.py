#!/usr/bin/env python3
"""
Direct PDF processor for Section F resumes.
This script processes PDFs directly from the Section F Resumes folder
without creating any sample files or test data.
"""

import os
import sys
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_pdf_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set up colored output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
ENDC = '\033[0m'

# Set up paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
PDF_DIR = ROOT_DIR / "backend" / "Section F Resumes"

# Check for environment variable that specifies .env path, otherwise use root directory
dotenv_path = os.getenv("DOTENV_PATH")
if dotenv_path:
    env_path = Path(dotenv_path)
    logger.info(f"Using .env file from specified path: {env_path}")
else:
    env_path = ROOT_DIR / ".env"
    logger.info(f"Using .env file from root directory: {env_path}")

# Load environment variables from the specified .env file
load_dotenv(env_path)

def log_step(step_name: str) -> None:
    """Log a step with formatting"""
    logger.info(f"{BLUE}{BOLD}===== {step_name} ====={ENDC}")

def log_success(message: str) -> None:
    """Log a success message with formatting"""
    logger.info(f"{GREEN}✓ {message}{ENDC}")

def log_error(message: str) -> None:
    """Log an error message with formatting"""
    logger.error(f"{RED}Error: {message}{ENDC}")

def log_warning(message: str) -> None:
    """Log a warning message with formatting"""
    logger.warning(f"{YELLOW}Warning: {message}{ENDC}")

def check_environment() -> bool:
    """
    Check that all required environment variables are set.
    
    Returns:
        True if all environment variables are set, False otherwise
    """
    log_step("Checking Environment Variables")
    
    required_vars = {
        "MISTRAL_API_KEY": "Mistral API key for PDF processing",
        "OPENAI_API_KEY": "OpenAI API key for embedding generation",
        "SUPABASE_PROJECT_URL": "Supabase project URL for database storage",
        "SUPABASE_PRIVATE_API_KEY": "Supabase private API key for database access"
    }
    
    missing_vars = []
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(f"{var_name} ({description})")
        else:
            logger.info(f"Found {var_name} in environment")
    
    if missing_vars:
        log_error(f"Missing environment variables: {', '.join(missing_vars)}")
        log_error(f"Please set these variables in your .env file at: {env_path}")
        return False
    
    log_success("All required environment variables are set")
    return True

def import_dependencies() -> bool:
    """
    Import all required dependencies.
    
    Returns:
        True if all dependencies are imported successfully, False otherwise
    """
    log_step("Importing Dependencies")
    
    required_modules = {
        "mistralai": "pip install mistralai",
        "openai": "pip install openai",
        "supabase": "pip install supabase",
        "pgvector": "pip install pgvector"
    }
    
    missing_modules = []
    
    for module_name, install_cmd in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(f"{module_name} ({install_cmd})")
    
    if missing_modules:
        log_error(f"Missing dependencies: {', '.join(missing_modules)}")
        log_error("Please install these packages with the commands shown above")
        return False
    
    log_success("All dependencies are installed")
    return True

def find_pdf_files() -> list:
    """
    Find all PDF files in the Section F Resumes directory.
    
    Returns:
        List of PDF file paths
    """
    log_step("Finding PDF Files")
    
    if not PDF_DIR.exists():
        log_error(f"PDF directory not found: {PDF_DIR}")
        return []
    
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        log_error(f"No PDF files found in {PDF_DIR}")
        return []
    
    log_success(f"Found {len(pdf_files)} PDF files")
    for pdf in pdf_files:
        logger.info(f"- {pdf.name}")
    
    return pdf_files

def process_pdf(pdf_path: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single PDF file and extract structured data.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Structured data as a dictionary, or None if processing failed
    """
    log_step(f"Processing PDF: {pdf_path.name}")
    
    try:
        # Import the process_pdf_file function from dataparser
        from dataparser import process_pdf_file
        
        # Process the PDF
        start_time = time.time()
        logger.info(f"Starting PDF processing at {time.strftime('%H:%M:%S')}")
        
        project_data = process_pdf_file(pdf_path)
        
        processing_time = time.time() - start_time
        logger.info(f"PDF processing completed in {processing_time:.2f} seconds")
        
        if not project_data:
            log_error(f"Failed to extract data from {pdf_path.name}")
            return None
        
        # Log extracted fields
        logger.info("Extracted the following data:")
        for key, value in project_data.items():
            if key != "firms_from_section_c":
                logger.info(f"- {key}: {value}")
            else:
                logger.info(f"- {key}: {len(value)} firms")
        
        log_success(f"Successfully processed PDF: {pdf_path.name}")
        return project_data
        
    except ImportError as e:
        log_error(f"Failed to import required modules: {str(e)}")
        return None
    except Exception as e:
        log_error(f"Error processing PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def upload_to_supabase(project_data: Dict[str, Any]) -> bool:
    """
    Upload project data to Supabase.
    
    Args:
        project_data: Project data dictionary
        
    Returns:
        True if upload was successful, False otherwise
    """
    log_step("Uploading to Supabase")
    
    try:
        # Import the required functions from datauploader
        from datauploader import upsert_project_in_supabase
        
        # Generate a project ID and title
        title = project_data.get("title_and_location", "Unknown Project")
        clean_title = title.lower().replace(" ", "_").replace(",", "").replace(".", "")
        project_id = f"proj_{clean_title[:30]}_{int(time.time())}"
        
        # Upload to Supabase
        start_time = time.time()
        logger.info(f"Starting upload at {time.strftime('%H:%M:%S')}")
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Project Title: {title}")
        
        success = upsert_project_in_supabase(project_id, title, project_data)
        
        upload_time = time.time() - start_time
        logger.info(f"Upload completed in {upload_time:.2f} seconds")
        
        if not success:
            log_error("Failed to upload project to Supabase")
            return False
        
        log_success("Successfully uploaded project to Supabase")
        return True
        
    except ImportError as e:
        log_error(f"Failed to import required modules: {str(e)}")
        return False
    except Exception as e:
        log_error(f"Error uploading to Supabase: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to run the processor"""
    log_step("Direct PDF Processor for Section F Resumes")
    
    # Check environment and dependencies
    if not check_environment() or not import_dependencies():
        sys.exit(1)
    
    # Find PDF files
    pdf_files = find_pdf_files()
    if not pdf_files:
        sys.exit(1)
    
    success_count = 0
    failure_count = 0
    
    # Process each PDF
    for pdf_file in pdf_files:
        # Process the PDF
        project_data = process_pdf(pdf_file)
        if not project_data:
            failure_count += 1
            continue
        
        # Upload to Supabase
        if upload_to_supabase(project_data):
            success_count += 1
        else:
            failure_count += 1
    
    # Summarize results
    log_step("Processing Summary")
    logger.info(f"Total PDFs: {len(pdf_files)}")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {failure_count}")
    
    if success_count == len(pdf_files):
        log_success("All PDFs processed successfully")
        return 0
    elif success_count > 0:
        log_warning("Some PDFs processed successfully, but others failed")
        return 2
    else:
        log_error("All PDFs failed to process")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log_error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 
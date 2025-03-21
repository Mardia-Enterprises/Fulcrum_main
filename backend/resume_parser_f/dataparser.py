#!/usr/bin/env python3
"""
Module for extracting structured data from Section F PDFs using Mistral AI API.
"""

import os
import sys
import json
import time
import random
import logging
import traceback
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

# Check for Mistral API key
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    logger.error("\033[91mError: MISTRAL_API_KEY not found in .env file\033[0m")
    logger.error("Please add your Mistral API key to the .env file in the root directory")
    sys.exit(1)

# Define fallback exception classes in case the import fails
class MistralAPIError(Exception):
    """Base exception for Mistral API errors."""
    pass

class RateLimitError(MistralAPIError):
    """Exception for rate limit errors."""
    pass

# Initialize Mistral client
try:
    # Import our compatibility layer
    from mistral_compat import get_mistral_client, MistralAPIError, RateLimitError
    
    # Initialize the client through our compatibility layer
    mistral_client = get_mistral_client(api_key=MISTRAL_API_KEY)
    logger.info("\033[92m✓ Mistral API client initialized\033[0m")
except ImportError:
    logger.error("\033[91mError: Failed to import Mistral AI client. Please install with 'pip install mistralai'\033[0m")
    sys.exit(1)
except Exception as e:
    logger.error(f"\033[91mError initializing Mistral client: {str(e)}\033[0m")
    sys.exit(1)

def upload_pdf_to_mistral(pdf_path: Union[str, Path]) -> Optional[str]:
    """
    Upload a PDF file to Mistral AI and return the URL.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        URL of the uploaded file, or None if upload failed
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.error(f"\033[91mError: PDF file not found: {pdf_path}\033[0m")
        return None
    
    logger.info(f"Uploading PDF to Mistral: {pdf_path.name}")
    
    try:
        # Open the file in binary mode and upload
        with open(pdf_path, "rb") as file:
            response = mistral_client.upload_file(file=file, file_name=pdf_path.name)
            
        # Get the file URL
        file_url = response.file_url
        logger.info(f"\033[92m✓ PDF uploaded successfully: {pdf_path.name}\033[0m")
        return file_url
    except Exception as e:
        logger.error(f"\033[91mError uploading PDF to Mistral: {str(e)}\033[0m")
        return None

def extract_structured_data_with_mistral(
    file_url: str, 
    max_retries: int = 5, 
    base_delay: float = 2.0
) -> Optional[Dict[str, Any]]:
    """
    Extract structured data from a PDF file using Mistral AI.
    Uses exponential backoff for retries on rate limit or server errors.
    
    Args:
        file_url: URL of the uploaded PDF file
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        
    Returns:
        Structured data as a dictionary, or None if extraction failed
    """
    if not file_url:
        logger.error("\033[91mError: No file URL provided\033[0m")
        return None
    
    logger.info("Extracting structured data from PDF...")
    
    # Create an output directory for JSON files
    output_dir = script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Prepare the system prompt
    system_prompt = """
    You are an expert at extracting structured information from SF330 Section F resume documents.
    Your task is to extract the following fields from the document in JSON format:
    
    - title_and_location: Extract the project title and location (usually at the top of the form)
    - year_completed: Extract the year completed for professional services and construction (if available)
    - project_owner: The name of the project owner
    - point_of_contact_name: The name of the point of contact
    - point_of_contact: The contact information (phone or email) for the point of contact
    - brief_description: Extract the full text of the project description
    - firms_from_section_c: A list of firms involved in the project, each with:
      - firm_name: The name of the firm
      - firm_location: The location of the firm
      - role: The role of the firm in the project (Prime, Sub, etc.)
    
    The output should be a valid JSON object with all these fields.
    Format year_completed as {"professional_services": YEAR, "construction": YEAR} where YEAR is an integer or null.
    Format firms_from_section_c as an array of objects with firm_name, firm_location, and role properties.
    Make sure to extract ALL firms mentioned in the document.
    """
    
    # Prepare the user message
    user_message = f"Please extract the structured information from this SF330 Section F document. File URL: {file_url}"
    
    # Define the extractable fields
    expected_fields = [
        "title_and_location",
        "year_completed",
        "project_owner",
        "point_of_contact_name",
        "point_of_contact",
        "brief_description",
        "firms_from_section_c"
    ]
    
    # Retry with exponential backoff
    attempt = 0
    while attempt < max_retries:
        try:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            
            if attempt > 1:
                logger.info(f"Retry attempt {attempt}/{max_retries} (delay: {delay:.2f}s)...")
                time.sleep(delay)
            
            # Make the API call
            logger.info(f"Sending PDF to Mistral (attempt {attempt}/{max_retries})...")
            response = mistral_client.chat(
                model="mistral-tiny",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,
                max_tokens=4096
            )
            
            # Extract the JSON response
            response_text = response.choices[0].message.content
            logger.info("Received response from Mistral, processing...")
            
            # Try to extract JSON from the response
            try:
                # First try to find JSON within the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}")
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end+1]
                    project_data = json.loads(json_str)
                else:
                    # If no JSON delimiters found, try to parse the entire response
                    project_data = json.loads(response_text)
                
                # Validate the extracted data
                missing_fields = [field for field in expected_fields if field not in project_data]
                if missing_fields:
                    logger.warning(f"\033[93mWarning: Missing fields in extracted data: {missing_fields}\033[0m")
                    
                    # If critical fields are missing, we might want to retry
                    if set(missing_fields) & {"title_and_location", "brief_description", "project_owner"}:
                        if attempt < max_retries:
                            logger.warning("Critical fields missing, retrying extraction...")
                            continue
                
                # Save the extracted data to a JSON file
                timestamp = int(time.time())
                json_filename = output_dir / f"project_data_{timestamp}.json"
                with open(json_filename, "w") as json_file:
                    json.dump(project_data, json_file, indent=2)
                logger.info(f"\033[92m✓ Extracted data saved to {json_filename}\033[0m")
                
                # Return the structured data
                return project_data
                
            except json.JSONDecodeError as e:
                logger.error(f"\033[91mError parsing JSON response: {str(e)}\033[0m")
                logger.error(f"Response text: {response_text[:200]}...")
                
                # Save the problematic response for debugging
                debug_dir = script_dir / "debug"
                debug_dir.mkdir(exist_ok=True)
                timestamp = int(time.time())
                with open(debug_dir / f"failed_response_{timestamp}.txt", "w") as f:
                    f.write(response_text)
                
                if attempt < max_retries:
                    continue
                else:
                    # Last attempt - try to salvage what we can
                    logger.warning("Attempting to salvage data from malformed response...")
                    return salvage_json_from_response(response_text, expected_fields)
                
        except RateLimitError as e:
            logger.warning(f"\033[93mRate limit error: {str(e)}\033[0m")
            if attempt < max_retries:
                logger.info(f"Waiting {delay:.2f}s before retrying...")
                time.sleep(delay)
            else:
                logger.error("\033[91mExceeded maximum retries for rate limit. Please try again later.\033[0m")
                return None
                
        except Exception as e:
            logger.error(f"\033[91mError extracting data with Mistral: {str(e)}\033[0m")
            logger.error(traceback.format_exc())
            if attempt < max_retries:
                logger.info(f"Waiting {delay:.2f}s before retrying...")
                time.sleep(delay)
            else:
                logger.error("\033[91mExceeded maximum retries. Extraction failed.\033[0m")
                return None
    
    logger.error("\033[91mAll extraction attempts failed\033[0m")
    return None

def salvage_json_from_response(response_text: str, expected_fields: List[str]) -> Dict[str, Any]:
    """
    Attempt to salvage JSON data from a malformed response.
    
    Args:
        response_text: The API response text
        expected_fields: List of expected fields in the JSON
        
    Returns:
        Salvaged data as a dictionary with as many fields as could be extracted
    """
    logger.info("Attempting to salvage JSON data from malformed response...")
    salvaged_data = {}
    
    # Try to extract JSON objects between braces
    import re
    json_pattern = r'(\{[^{]*?\})'
    json_matches = re.findall(json_pattern, response_text)
    
    # Try each potential JSON object
    for json_str in json_matches:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                # If this object has any of our expected fields, merge it
                if any(field in data for field in expected_fields):
                    for field in expected_fields:
                        if field in data:
                            salvaged_data[field] = data[field]
        except:
            continue
    
    # If we found some fields, consider it a partial success
    if salvaged_data:
        logger.info(f"\033[93mPartially salvaged data with {len(salvaged_data)} fields\033[0m")
        
        # Add placeholder values for missing critical fields
        if "title_and_location" not in salvaged_data:
            salvaged_data["title_and_location"] = "Unknown Project"
        if "project_owner" not in salvaged_data:
            salvaged_data["project_owner"] = "Unknown Owner"
        if "brief_description" not in salvaged_data:
            salvaged_data["brief_description"] = "No description available"
        if "year_completed" not in salvaged_data:
            salvaged_data["year_completed"] = {"professional_services": None, "construction": None}
        if "firms_from_section_c" not in salvaged_data:
            salvaged_data["firms_from_section_c"] = []
            
        return salvaged_data
    
    # If salvage completely failed, return a minimal valid structure
    logger.warning("\033[93mSalvage failed. Returning minimal structure.\033[0m")
    return {
        "title_and_location": "Error: Extraction Failed",
        "year_completed": {"professional_services": None, "construction": None},
        "project_owner": "Unknown",
        "point_of_contact_name": "Unknown",
        "point_of_contact": "Unknown",
        "brief_description": "Error extracting data from PDF",
        "firms_from_section_c": []
    }

def process_pdf_file(pdf_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Process a single PDF file and extract structured data.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Structured data as a dictionary, or None if processing failed
    """
    pdf_path = Path(pdf_path)
    logger.info(f"\n\033[1;36m===== Processing PDF: {pdf_path.name} =====\033[0m")
    
    # Step 1: Upload PDF to Mistral
    logger.info("Step 1: Uploading PDF to Mistral...")
    file_url = upload_pdf_to_mistral(pdf_path)
    if not file_url:
        logger.error(f"\033[91mFailed to upload PDF: {pdf_path.name}\033[0m")
        return None
    
    # Step 2: Extract structured data
    logger.info("Step 2: Extracting structured data...")
    project_data = extract_structured_data_with_mistral(file_url)
    if not project_data:
        logger.error(f"\033[91mFailed to extract structured data: {pdf_path.name}\033[0m")
        return None
    
    logger.info(f"\033[92m✓ Successfully processed PDF: {pdf_path.name}\033[0m")
    return project_data

def process_pdf_directory(
    pdf_dir: Union[str, Path], 
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process all PDF files in a directory.
    
    Args:
        pdf_dir: Directory containing PDF files
        limit: Maximum number of PDFs to process (None for all)
        
    Returns:
        List of structured data dictionaries for successfully processed PDFs
    """
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"\033[91mError: PDF directory not found: {pdf_dir}\033[0m")
        return []
    
    logger.info(f"\n\033[1;36m===== Processing PDFs in: {pdf_dir} =====\033[0m")
    
    # Find all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"\033[93mNo PDF files found in {pdf_dir}\033[0m")
        return []
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    if limit:
        pdf_files = pdf_files[:limit]
        logger.info(f"Processing first {limit} PDF files")
    
    # Process each PDF file
    results = []
    for i, pdf_file in enumerate(pdf_files):
        logger.info(f"\nProcessing file {i+1}/{len(pdf_files)}: {pdf_file.name}")
        
        try:
            project_data = process_pdf_file(pdf_file)
            if project_data:
                results.append(project_data)
                
                # Add a small delay between processing to avoid rate limits
                if i < len(pdf_files) - 1:
                    time.sleep(2)
        except Exception as e:
            logger.error(f"\033[91mError processing {pdf_file.name}: {str(e)}\033[0m")
            logger.error(traceback.format_exc())
    
    logger.info(f"\n\033[1;36m===== Processing Summary =====\033[0m")
    logger.info(f"Total PDFs: {len(pdf_files)}")
    logger.info(f"Successfully processed: {len(results)}")
    logger.info(f"Failed: {len(pdf_files) - len(results)}")
    
    return results

if __name__ == "__main__":
    # If run directly, process PDFs in the specified directory
    if len(sys.argv) > 1:
        pdf_dir = sys.argv[1]
    else:
        # Default to "Section F Resumes" directory in the project root
        pdf_dir = script_dir.parent / "Section F Resumes"
    
    logger.info(f"Processing PDFs in {pdf_dir}")
    results = process_pdf_directory(pdf_dir)
    logger.info(f"Processed {len(results)} PDFs successfully") 
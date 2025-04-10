import os
import re
import uuid
import tempfile
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import logging
import base64
import json
import sys  # For sys.exit on critical errors

# PDF processing libraries
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# API clients - Using Mistral client
try:
    # Import Mistral client for version 0.0.7
    from mistralai.client import MistralClient as Mistral
    logger = logging.getLogger("pdf_processor_projects")
    logger.info("Mistral client successfully imported")
except ImportError as e:
    logger = logging.getLogger("pdf_processor_projects")
    logger.error(f"Failed to import Mistral client: {e}")
    logger.error("Please ensure mistralai>=0.0.7 is installed")

from openai import OpenAI

# Supabase
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pdf_processor_projects")

# Load environment variables
load_dotenv()

# Configure Supabase client with updated environment variable names
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
if not supabase_url or not supabase_key:
    logger.error("Supabase credentials not found in .env file")
    logger.error("Please set SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY in your .env file")
    supabase = None
else:
    try:
        # Try to create the Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by making a simple query
        try:
            # Try to list storage buckets to verify connection and permissions
            storage_buckets = supabase.storage.list_buckets()
            logger.info(f"Successfully connected to Supabase")
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"Supabase RLS policy issue: {e}")
                logger.error("Please ensure your Supabase service key has proper RLS policies enabled")
                logger.error("You may need to create policies in Supabase for the tables and storage buckets")
            else:
                logger.error(f"Failed to connect to Supabase: {e}")
            supabase = None
            
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None

# Configure AI clients
mistral_api_key = os.getenv("MISTRAL_API_KEY")
if not mistral_api_key:
    logger.error("Mistral API key not found in .env file")
    logger.error("Please set MISTRAL_API_KEY in your .env file")
    logger.error("Mistral is required for this application")
    mistral_client = None
else:
    try:
        # Initialize Mistral client for version 0.0.7
        mistral_client = Mistral(api_key=mistral_api_key)
        
        # Define model after initialization
        mistral_model = os.getenv("MISTRAL_MODEL", "mistral-small")
        
        # Test the API key with a minimal request (if needed)
        try:
            # Simple test using direct chat method for 0.0.7
            logger.info("Verifying Mistral API key...")
            test_response = mistral_client.chat(
                model=mistral_model,
                messages=[{"role": "user", "content": "Hello"}]
            )
            logger.info("Successfully verified Mistral API connection")
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str:
                logger.error(f"Failed to authenticate with Mistral API: {e}")
                logger.error("Authentication error with your API key")
                logger.error("Please verify your key at https://console.mistral.ai/api-keys/")
            else:
                logger.error(f"Failed to connect to Mistral API: {e}")
            
            # Keep the client object even if test fails - it might work for other endpoints
            logger.warning("Proceeding with Mistral client despite test failure")
            
    except Exception as e:
        logger.error(f"Failed to initialize Mistral client: {e}")
        logger.error(f"Error details: {str(e)}")
        mistral_client = None

# OpenAI is required as the primary AI service
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OpenAI API key not found in .env file")
    logger.error("OpenAI is required for this application")
    openai_client = None
else:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        openai_embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Test the API key with a minimal request for embeddings
        try:
            test_embedding = openai_client.embeddings.create(
                model=openai_embedding_model,
                input="Hello, this is a test."
            )
            logger.info("Successfully verified OpenAI API connection")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            logger.error("OpenAI is required for this application")
            openai_client = None
            
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None

# Document storage bucket name
DOCUMENTS_BUCKET = "documents"

def verify_environment(skip_bucket_check=False):
    """
    Verify that all required components are available
    
    Args:
        skip_bucket_check: If True, skip checking for storage bucket
        
    Returns:
        bool: True if environment is properly configured, False otherwise
    """
    all_requirements_met = True
    
    # Check Supabase connection
    if not supabase:
        logger.error("Supabase client is not configured properly")
        logger.error("Please check your SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY in the .env file")
        all_requirements_met = False
    
    # OpenAI is required
    if not openai_client:
        logger.error("OpenAI client is not configured properly")
        logger.error("OpenAI is required for this application")
        
        if not openai_api_key:
            logger.error("No OPENAI_API_KEY found in your .env file")
        else:
            logger.error("Your OPENAI_API_KEY was found but connection failed")
            logger.error("Please ensure your OpenAI API key is valid and has not expired")
            
        logger.error("To fix this issue:")
        logger.error("1. Visit https://platform.openai.com/api-keys to verify your API key")
        logger.error("2. Update the OPENAI_API_KEY in your .env file")
        
        all_requirements_met = False
    
    # Mistral is optional
    if not mistral_client:
        logger.warning("Mistral client is not configured properly")
        logger.warning("Mistral features will not be available")
    
    # Verify Tesseract OCR is installed
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception as e:
        logger.error(f"Tesseract OCR is not properly installed: {e}")
        logger.error("Please install Tesseract OCR following the instructions in the README")
        all_requirements_met = False
    
    # Verify database schema for employee_projects table
    if supabase:
        try:
            # Check if employee_projects table has the necessary text_id column
            logger.info("Checking employee_projects table schema...")
            schema_info = supabase.table('employee_projects').select('*').limit(1).execute()
            
            # If we have data, check columns directly
            if schema_info.data:
                columns = schema_info.data[0].keys()
                if 'text_id' not in columns:
                    logger.error("Missing required 'text_id' column in employee_projects table")
                    logger.error("Please ensure your database schema is up to date")
                    all_requirements_met = False
                else:
                    logger.info("Found 'text_id' column in employee_projects table")
            else:
                # If no data exists yet, try a different approach by trying a minimal query
                logger.info("No data in employee_projects table, testing structure with minimal query...")
                try:
                    # Try a minimal query that should work if schema is correct
                    test_query = supabase.table('employee_projects').select('employee_id, project_id, text_id').limit(1).execute()
                    logger.info("employee_projects table schema verification passed")
                except Exception as e:
                    if 'text_id' in str(e).lower():
                        logger.error("Missing required 'text_id' column in employee_projects table")
                        logger.error("Please ensure your database schema is up to date")
                        all_requirements_met = False
                    else:
                        # Something else is wrong with the query but not necessarily the text_id column
                        logger.warning(f"Could not fully verify employee_projects table schema: {e}")
                
        except Exception as e:
            logger.warning(f"Could not verify employee_projects table schema: {e}")
    
    # Check if the documents bucket exists in Supabase
    if supabase and not skip_bucket_check:
        try:
            # Get list of buckets
            buckets = supabase.storage.list_buckets()
            
            # Check if documents bucket exists in the list
            bucket_exists = False
            
            if not buckets:
                logger.error("No storage buckets returned from Supabase")
                logger.error("Please ensure your Supabase service key has access to storage")
                all_requirements_met = False
            else:
                logger.info(f"Checking for '{DOCUMENTS_BUCKET}' bucket in Supabase storage")
                
                # Try different ways to extract bucket names based on return type
                for bucket in buckets:
                    bucket_name = None
                    
                    if isinstance(bucket, dict):
                        bucket_name = bucket.get('name')
                    elif hasattr(bucket, 'name'):
                        bucket_name = bucket.name
                    elif hasattr(bucket, 'id'):
                        bucket_name = bucket.id  # Sometimes id is used instead of name
                    else:
                        # Try string representation as last resort
                        bucket_name = str(bucket)
                    
                    if bucket_name == DOCUMENTS_BUCKET:
                        bucket_exists = True
                        logger.info(f"Found '{DOCUMENTS_BUCKET}' bucket in Supabase storage")
                        break
                
                if not bucket_exists:
                    logger.error(f"Storage bucket '{DOCUMENTS_BUCKET}' not found in Supabase")
                    logger.error(f"The '{DOCUMENTS_BUCKET}' bucket must exist in Supabase Storage")
                    logger.error(f"Found buckets: {[str(b) for b in buckets]}")
                    all_requirements_met = False
                
        except Exception as e:
            logger.error(f"Error checking Supabase storage buckets: {e}")
            all_requirements_met = False
    
    return all_requirements_met 

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF and perform OCR if needed.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    doc = fitz.open(file_path)
    text_content = []
    
    for page_num, page in enumerate(doc):
        # Try to get text directly
        text = page.get_text()
        
        # If minimal text is extracted, try OCR
        if len(text.strip()) < 50:  # Arbitrary threshold
            logger.info(f"Using OCR for page {page_num+1}")
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
        
        text_content.append(text)
    
    doc.close()
    return "\n".join(text_content)


def extract_project_and_firms_chunks(text: str) -> Dict[str, str]:
    """
    Extract project section and firms section from the full text.
    The project section is expected to be the first section.
    The firms section is expected to be in section C.
    
    Args:
        text: Full text extracted from PDF
        
    Returns:
        Dictionary with project_chunk and firms_chunk
    """
    logger.info("Extracting project and firms chunks from text")
    
    result = {
        "project_chunk": "",
        "firms_chunk": ""
    }
    
    # Split the text into sections based on common section markers
    # Looking for Section headings like "SECTION A", "SECTION B", etc.
    section_pattern = r'(?i)(?:SECTION|Section)\s+([A-Z])[:\s]+(.*?)(?=(?:SECTION|Section)\s+[A-Z][:\s]+|\Z)'
    
    # Find all sections
    sections = re.findall(section_pattern, text, re.DOTALL)
    
    if not sections:
        logger.warning("No sections found using standard pattern, using alternative method")
        # Alternative approach: just look for the first portion of the document as project
        # and anything mentioning "firms" or "consultants" as firms section
        
        # Take first 30% of document as project section
        text_length = len(text)
        project_end = int(text_length * 0.3)
        result["project_chunk"] = text[:project_end].strip()
        
        # Look for firms or consultants section
        firms_keywords = ["firms", "consultants", "section c", "Section C"]
        firms_section = ""
        
        for keyword in firms_keywords:
            if keyword.lower() in text.lower():
                # Find the position of the keyword
                pos = text.lower().find(keyword.lower())
                # Take text from this position up to 30% of the text length
                firms_end = min(pos + int(text_length * 0.3), text_length)
                firms_section = text[pos:firms_end].strip()
                break
        
        result["firms_chunk"] = firms_section
        
        logger.warning("Used approximate chunking method")
    else:
        logger.info(f"Found {len(sections)} sections in the document")
        
        # Find the project section (assumed to be the first section or section A)
        project_section = None
        for section_letter, section_content in sections:
            if section_letter.upper() == 'A' or section_letter.upper() == 'F':
                project_section = section_content.strip()
                logger.info(f"Found project section in Section {section_letter}")
                break
        
        # If no Section A/F found, use the first section
        if not project_section and sections:
            project_section = sections[0][1].strip()
            logger.info(f"Using first section (Section {sections[0][0]}) as project section")
        
        # Find the firms section (should be in Section C)
        firms_section = None
        for section_letter, section_content in sections:
            if section_letter.upper() == 'C':
                firms_section = section_content.strip()
                logger.info("Found firms section in Section C")
                break
        
        # Store the results
        result["project_chunk"] = project_section if project_section else ""
        result["firms_chunk"] = firms_section if firms_section else ""
    
    # Check if we found meaningful chunks
    if not result["project_chunk"]:
        logger.warning("Failed to extract project chunk")
    else:
        logger.info(f"Extracted project chunk ({len(result['project_chunk'])} characters)")
    
    if not result["firms_chunk"]:
        logger.warning("Failed to extract firms chunk")
    else:
        logger.info(f"Extracted firms chunk ({len(result['firms_chunk'])} characters)")
    
    return result 

def process_with_ai(chunks: Dict[str, str], use_mistral: bool = False) -> Dict[str, Any]:
    """
    Process the extracted chunks using OpenAI by default, with optional Mistral
    
    Args:
        chunks: Dictionary containing project_chunk and firms_chunk
        use_mistral: Whether to try using Mistral first (default: False)
        
    Returns:
        Structured data containing project and firms information
    """
    logger.info("Processing extracted chunks with AI")
    
    system_prompt = """
    You are an expert at extracting structured information from project documents.
    Extract the following information from the provided document sections:
    
    1. Project information (from the project section): 
       - name: The full name of the project
       - location: The location of the project
    
    2. Firms and Team Members information (from the firms section):
       - firms: A detailed list of company and individual names with their precise roles/titles
    
    For the firms and individuals list, please:
    - Include all individual personnel names (e.g., "John Doe", "Josh Carson", "Don Daigle") 
    - Include all company names (e.g., "ABC Engineering", "XYZ Construction")
    - Pay special attention to professional designations and titles that appear with names:
      * Engineering designations: PE, P.E., Professional Engineer, etc.
      * Project roles: PM, Project Manager, Lead, Director, etc.
      * Technical specialties: Civil, Structural, Mechanical, Electrical, etc.
    - Extract the exact role/title as it appears in the document
    - Return each name with the most specific role/title mentioned
    
    Return the information as a JSON object with the following structure:
    {
        "project": {
            "name": "Project Name",
            "location": "Project Location"
        },
        "firms": [
            {"name": "Firm 1", "role": "Prime Contractor"},
            {"name": "John Doe", "role": "PE"},
            {"name": "Jane Smith", "role": "Electrical Engineer"},
            {"name": "Firm 2", "role": "Subcontractor"}
        ]
    }
    
    Important guidelines for extracting roles:
    1. Be precise - extract the EXACT role/title as written in the document
    2. If multiple roles appear for a person, use the most specific one
    3. For designations like "PE" or "CVS", use them exactly as they appear
    4. If a role includes a specialty (like "Civil Engineer"), include the full description
    5. If no role is mentioned, use "Contributor" as the default
    
    The accuracy of the roles is extremely important for database integration.
    """
    
    # Combine chunks with clear separation for the AI
    combined_text = f"PROJECT SECTION:\n{chunks['project_chunk']}\n\nFIRMS SECTION:\n{chunks['firms_chunk']}"
    
    # Try with Mistral if available and requested
    if use_mistral and mistral_client:
        try:
            logger.info("Attempting to process with Mistral AI")
            
            # Create messages for mistralai
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_text}
            ]
            
            # Try to call Mistral API
            response = mistral_client.chat(
                model=mistral_model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            # Extract content from response
            json_text = response.choices[0].message.content
            
            try:
                structured_data = json.loads(json_text)
                logger.info("Successfully processed with Mistral AI")
                return structured_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Mistral JSON response: {e}")
                logger.error(f"Raw result: {json_text[:200]}...")
                logger.warning("Falling back to OpenAI")
                    
        except Exception as e:
            logger.error(f"Error with Mistral AI: {e}")
            logger.warning("Falling back to OpenAI")
    
    # Use OpenAI (primary or fallback)
    if openai_client:
        try:
            logger.info("Processing with OpenAI")
            response = openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": combined_text}
                ],
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            try:
                parsed_data = json.loads(result)
                logger.info("Successfully processed with OpenAI")
                return parsed_data
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing OpenAI JSON response: {e}")
                logger.error(f"Raw result: {result[:200]}...")
                raise RuntimeError(f"Failed to parse OpenAI response as JSON: {e}")
            
        except Exception as e:
            logger.error(f"Error with OpenAI: {e}")
            raise RuntimeError(f"Failed to process document with OpenAI: {e}")
    else:
        # No AI processing service available
        error_msg = "No AI processing service available"
        logger.error(error_msg)
        raise RuntimeError(error_msg) 

def find_matching_teams(firms: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Find employees in the database that match the extracted firm names
    
    Args:
        firms: List of firm dictionaries with name and role extracted from the document
        
    Returns:
        List of matching employee objects from the database with roles
    """
    if not supabase:
        logger.error("Supabase client not available, cannot match employees")
        return []
    
    if not firms:
        logger.warning("No firms provided for matching")
        return []
    
    matching_employees = []
    roles_by_employee_id = {}  # Track the most specific role for each employee
    
    try:
        # Get all employees from the database
        employees_result = supabase.table('employee').select('*').execute()
        employees = employees_result.data
        
        if not employees:
            logger.warning("No employees found in database for matching")
            return []
        
        logger.info(f"Found {len(employees)} employees in database")
        logger.info(f"Matching against {len(firms)} extracted firms/individuals")
        
        # Log the exact names and roles we're looking for
        employee_names = [employee.get('name', '') for employee in employees]
        firm_details = [f"{firm.get('name', '')} ({firm.get('role', 'Unknown')})" for firm in firms]
        
        logger.info(f"Employees in database: {employee_names}")
        logger.info(f"Firms/individuals to match: {firm_details}")
        
        # Helper function to normalize names for comparison
        def normalize_name(name):
            if not name:
                return ""
            # Convert to lowercase, remove common titles, remove extra whitespace
            normalized = name.lower().strip()
            # Remove common titles and qualifications for comparison purpose only
            titles = ["dr.", "mr.", "mrs.", "ms.", "prof.", "pe", "cvs", "ccp", "p.e."]
            for title in titles:
                normalized = normalized.replace(f"{title} ", " ").replace(f" {title}", " ")
            # Remove extra spaces
            normalized = " ".join(normalized.split())
            return normalized
        
        # Process each firm/individual from the document
        for firm in firms:
            firm_name = firm.get('name', '').strip()
            firm_role = firm.get('role', 'Contributor')
            
            if not firm_name:
                continue
                
            firm_normalized = normalize_name(firm_name)
            logger.info(f"Checking firm/individual: '{firm_name}' with role '{firm_role}', normalized: '{firm_normalized}'")
            
            # Look for matching employees
            for employee in employees:
                employee_id = employee.get('id')
                employee_name = employee.get('name', '').strip()
                employee_normalized = normalize_name(employee_name)
                
                # Check for exact match first
                if employee_normalized == firm_normalized:
                    logger.info(f"Found exact match: '{employee_name}' for: '{firm_name}' with role '{firm_role}'")
                    # Create a copy of the employee and add the role from the document
                    employee_with_role = employee.copy()
                    employee_with_role['project_role'] = firm_role
                    
                    # Add to matching employees if not already included
                    if not any(e.get('id') == employee_id for e in matching_employees):
                        matching_employees.append(employee_with_role)
                    
                    # Update the role (may replace if this is a more specific match)
                    roles_by_employee_id[employee_id] = firm_role
                    continue
                
                # Check if one name contains the other
                if employee_normalized and firm_normalized and (
                   employee_normalized in firm_normalized or firm_normalized in employee_normalized):
                    
                    # For individual names, check if words match in order
                    employee_parts = employee_normalized.split()
                    if len(employee_parts) > 1 and all(part in firm_normalized for part in employee_parts):
                        # Check if parts appear in same order
                        employee_pos = [firm_normalized.find(part) for part in employee_parts if part in firm_normalized]
                        if employee_pos == sorted(employee_pos) and len(set(employee_pos)) == len(employee_pos):
                            logger.info(f"Found name match: '{employee_name}' in '{firm_name}' with role '{firm_role}'")
                            
                            # Create a copy of the employee and add the role
                            employee_with_role = employee.copy()
                            employee_with_role['project_role'] = firm_role
                            
                            # Add to matching employees if not already included
                            if not any(e.get('id') == employee_id for e in matching_employees):
                                matching_employees.append(employee_with_role)
                            
                            # Update the role if not already set or if this one is more specific
                            current_role = roles_by_employee_id.get(employee_id, "")
                            # Prefer roles that aren't just "Contributor" 
                            if current_role == "" or current_role == "Contributor" or len(firm_role) > len(current_role):
                                roles_by_employee_id[employee_id] = firm_role
                                
                            continue
        
        # Update all matched employees with their best roles
        for employee in matching_employees:
            employee_id = employee.get('id')
            if employee_id in roles_by_employee_id:
                employee['project_role'] = roles_by_employee_id[employee_id]
        
        # Log the final results
        if matching_employees:
            match_details = [f"{e.get('name', '')} as '{e.get('project_role', 'Contributor')}'" 
                            for e in matching_employees]
            logger.info(f"Found {len(matching_employees)} matching employees with roles: {match_details}")
        else:
            logger.warning("No matching employees found")
        
        return matching_employees
        
    except Exception as e:
        logger.error(f"Error finding matching employees: {e}")
        logger.error(f"Exception details: {str(e)}")
        return []


def generate_embeddings(text: str) -> List[float]:
    """
    Generate embedding vector for text using OpenAI's embeddings API
    
    Args:
        text: Text to generate embeddings for
        
    Returns:
        List of floats representing the embedding vector
    """
    if not openai_client:
        logger.warning("OpenAI client not available for embeddings, using empty vector")
        return [0.0] * 1536  # Default size for OpenAI embeddings
        
    try:
        response = openai_client.embeddings.create(
            model=openai_embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return empty embedding as fallback
        return [0.0] * 1536  # Default size for OpenAI embeddings 

def extract_roles_from_text(names: List[str], text: str) -> Dict[str, str]:
    """
    Attempt to extract roles directly from document text for each name
    
    Args:
        names: List of names to search for in the text
        text: The document text to search in
        
    Returns:
        Dictionary mapping names to their roles
    """
    roles_by_name = {}
    common_roles = [
        "PE", "P.E.", "CVS", "PMP", "LEED AP", "RA", "CCP", 
        "Project Manager", "PM", "Engineer", "Director",
        "Principal", "Lead", "Civil", "Structural", "Mechanical", 
        "Electrical", "Environmental", "QA/QC", "Inspector"
    ]
    
    # Normalize text for searching
    text_lower = text.lower()
    
    # Search for each name in the text
    for name in names:
        if not name:
            continue
            
        name_lower = name.lower()
        
        # Find all occurrences of the name in the text
        name_positions = []
        pos = text_lower.find(name_lower, 0)
        while pos >= 0:
            name_positions.append(pos)
            pos = text_lower.find(name_lower, pos + 1)
        
        if not name_positions:
            continue
            
        # Look for roles near each occurrence of the name
        roles_found = []
        
        for pos in name_positions:
            # Extract a context window around the name
            start = max(0, pos - 30)
            end = min(len(text), pos + len(name) + 30)
            context = text[start:end]
            
            # Check for common roles in this context
            for role in common_roles:
                role_lower = role.lower()
                if role_lower in context.lower():
                    # Check if the role is close to the name (after or right before)
                    role_pos = context.lower().find(role_lower)
                    name_in_context_pos = context.lower().find(name_lower)
                    
                    # If role appears close to the name (within 15 chars), capture it
                    if abs(role_pos - name_in_context_pos) < 15:
                        # Get the exact case of the role from the original text
                        role_start = start + role_pos
                        role_end = role_start + len(role)
                        exact_role = text[role_start:role_end]
                        roles_found.append(exact_role)
                        break
                        
            # Also look for direct patterns like "Name, PE" or "Name (PE)"
            patterns = [
                rf"{re.escape(name)},?\s+([A-Z]{{2,}}(?:\.)?)", # Name, PE or Name PE
                rf"{re.escape(name)}\s+\(([A-Z]{{2,}}(?:\.)?)\)",     # Name (PE)
                rf"{re.escape(name)}\s+is\s+(?:a|the)\s+(.+?)[,\.]",  # Name is a/the Role
                rf"{re.escape(name)},\s+([^,\.]+?(?:Engineer|Manager|Director|Lead|Specialist|Consultant))[,\.]", # Name, Civil Engineer
                rf"([A-Za-z/]+\s+(?:Engineer|Manager|Director|Lead|Specialist|Consultant))\s+{re.escape(name)}"  # Civil Engineer Name
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.group(1):
                        roles_found.append(match.group(1))
        
        # If we found roles, use the most specific one
        if roles_found:
            # Define priority scoring for roles (higher = more specific)
            def get_role_priority(role):
                # Exact professional designations get highest priority
                if re.match(r'^[A-Z]{2,}(?:\.)?$', role):  # PE, P.E., CVS, etc.
                    return 100
                
                # Roles with qualifiers are more specific (Civil Engineer > Engineer)
                if ' ' in role and any(term in role.lower() for term in ['engineer', 'manager', 'director']):
                    return 80
                
                # Regular professional roles
                if any(term in role.lower() for term in ['engineer', 'manager', 'director', 'lead']):
                    return 60
                
                # Default priority based on length (longer = more specific)
                return len(role)
                
            # Sort by priority then by length
            roles_found.sort(key=lambda r: (get_role_priority(r), len(r)), reverse=True)
            roles_by_name[name] = roles_found[0]
            logger.info(f"Extracted role from text for {name}: '{roles_found[0]}'")
            if len(roles_found) > 1:
                logger.info(f"Other potential roles found: {roles_found[1:]}")
        
    return roles_by_name

def upload_to_supabase(
    pdf_path: str, 
    chunks: Dict[str, str],
    structured_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Upload original PDF and processed data to Supabase
    
    Args:
        pdf_path: Path to the PDF file
        chunks: Dictionary containing project_chunk and firms_chunk
        structured_data: Processed data from AI
        
    Returns:
        Dictionary with status and IDs of created resources
    """
    if not supabase:
        error_msg = "Supabase client not available, cannot upload data"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    logger.info(f"Uploading project PDF and processed data to Supabase: {pdf_path}")
    
    result = {
        "status": "success",
        "document_id": None,
        "project_id": None,
        "project_chunk_id": None,
        "firms_chunk_id": None,
        "matching_employee_ids": [],
        "employee_project_relationships": []
    }
    
    try:
        # 1. Upload PDF to storage
        pdf_name = os.path.basename(pdf_path)
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        storage_path = f"{uuid.uuid4()}/{pdf_name}"
        
        try:
            # Upload to documents bucket
            upload_result = supabase.storage.from_(DOCUMENTS_BUCKET).upload(
                path=storage_path,
                file=pdf_content,
                file_options={"content-type": "application/pdf"}
            )
            logger.info(f"Successfully uploaded PDF to storage: {storage_path}")
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error uploading PDF: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for storage")
                raise RuntimeError("Supabase RLS policy error uploading PDF - please check your Supabase configuration")
            else:
                logger.error(f"Error uploading PDF to storage: {e}")
                raise
        
        # Get public URL
        try:
            # Get the public URL for the uploaded file
            pdf_url = supabase.storage.from_(DOCUMENTS_BUCKET).get_public_url(storage_path)
            logger.info(f"Got public URL: {pdf_url}")
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            # Construct URL manually as fallback
            supabase_project_url = os.getenv("SUPABASE_PROJECT_URL")
            pdf_url = f"{supabase_project_url}/storage/v1/object/public/{DOCUMENTS_BUCKET}/{storage_path}"
            logger.warning(f"Using constructed URL instead: {pdf_url}")
        
        # 2. Insert document into documents table
        try:
            document_result = supabase.table('documents').insert({
                "pdf_name": pdf_name,
                "document_link": pdf_url
            }).execute()
            
            if not document_result.data:
                raise RuntimeError("No data returned from document insert")
                
            document_id = document_result.data[0]['id']
            result["document_id"] = document_id
            logger.info(f"Inserted document record with ID: {document_id}")
            
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting document: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the documents table")
                raise RuntimeError("Supabase RLS policy error inserting document - please check your Supabase policies")
            else:
                logger.error(f"Error inserting document record: {e}")
                raise
        
        # 3. Insert project data
        try:
            project_data = structured_data.get("project", {})
            project_embedding = generate_embeddings(chunks["project_chunk"])
            
            project_result = supabase.table('projects').insert({
                "name": project_data.get("name"),
                "location": project_data.get("location")
            }).execute()
            
            if not project_result.data:
                raise RuntimeError("No data returned from project insert")
                
            project_id = project_result.data[0]['id']
            result["project_id"] = project_id
            logger.info(f"Inserted project record with ID: {project_id}")
        
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting project: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the projects table")
                raise RuntimeError("Supabase RLS policy error inserting project - please check your Supabase policies")
            else:
                logger.error(f"Error inserting project record: {e}")
                raise
        
        # 4. Insert project chunk into sharded_documents
        try:
            if chunks["project_chunk"]:
                project_chunk_text = chunks["project_chunk"]
                chunk_embedding = generate_embeddings(project_chunk_text)
                
                project_chunk_result = supabase.table('sharded_documents').insert({
                    "document_id": document_id,
                    "text": project_chunk_text,
                    "embedding": chunk_embedding
                }).execute()
                
                if project_chunk_result.data:
                    project_chunk_id = project_chunk_result.data[0]['text_id']
                    result["project_chunk_id"] = project_chunk_id
                    logger.info(f"Stored project chunk in sharded_documents with ID: {project_chunk_id}")
                    
                    # Link project to document using the project chunk text_id
                    supabase.table('project_documents').insert({
                        "project_id": project_id,
                        "text_id": project_chunk_id  # Use text_id from sharded_documents
                    }).execute()
                    logger.info(f"Linked project {project_id} to document using sharded text_id: {project_chunk_id}")
                else:
                    logger.warning("Project chunk insert returned no data")
            else:
                logger.warning("No project chunk data found")
                
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting project chunk: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the sharded_documents table")
            else:
                logger.error(f"Error inserting project chunk: {e}")
            # Continue anyway as sharded documents are supplementary
        
        # 6. Insert firms chunk into sharded_documents
        try:
            if chunks["firms_chunk"]:
                firms_chunk_text = chunks["firms_chunk"]
                chunk_embedding = generate_embeddings(firms_chunk_text)
                
                firms_chunk_result = supabase.table('sharded_documents').insert({
                    "document_id": document_id,
                    "text": firms_chunk_text,
                    "embedding": chunk_embedding
                }).execute()
                
                if firms_chunk_result.data:
                    firms_chunk_id = firms_chunk_result.data[0]['text_id']
                    result["firms_chunk_id"] = firms_chunk_id
                    logger.info(f"Stored firms chunk in sharded_documents with ID: {firms_chunk_id}")
                else:
                    logger.warning("Firms chunk insert returned no data")
            else:
                logger.warning("No firms chunk data found")
                
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting firms chunk: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the sharded_documents table")
            else:
                logger.error(f"Error inserting firms chunk: {e}")
            # Continue anyway as sharded documents are supplementary
        
        # 7. Find matching employees and create employee-project relationships
        try:
            # Get firms from structured data
            firms = structured_data.get("firms", [])
            
            # Extract employee roles directly from text
            employee_names = []
            employees_result = supabase.table('employee').select('*').execute()
            if employees_result.data:
                employee_names = [employee.get('name', '') for employee in employees_result.data if employee.get('name')]
                
            # Extract roles by directly analyzing the firms section text
            direct_roles = {}
            if employee_names and chunks.get("firms_chunk"):
                logger.info("Attempting to extract roles directly from firms text...")
                direct_roles = extract_roles_from_text(employee_names, chunks.get("firms_chunk", ""))
                if direct_roles:
                    logger.info(f"Successfully extracted {len(direct_roles)} roles directly from text: {direct_roles}")
            
            # Find employees that match the firm names
            matching_employees = find_matching_teams(firms)
            
            # Store the matching employee IDs in the result
            for employee in matching_employees:
                employee_id = employee.get('id')
                employee_name = employee.get('name', '')
                result["matching_employee_ids"].append(employee_id)
                
                # Check if we found a direct role from text
                if employee_name in direct_roles:
                    # Override the role with directly extracted one
                    employee['project_role'] = direct_roles[employee_name]
                    logger.info(f"Using directly extracted role for {employee_name}: {direct_roles[employee_name]}")
                
                # Create relationship for each matching employee with the project
                try:
                    # Use only project_chunk_id as text_id for employee_projects
                    if result["project_chunk_id"]:
                        # Determine the best role to use (prioritize directly extracted role)
                        if employee_name in direct_roles:
                            employee_role = direct_roles[employee_name]
                        else:
                            # Fall back to role from AI extraction or employee database
                            employee_role = employee.get('project_role', employee.get('role', 'Contributor'))
                        
                        # Insert employee-project relationship with role
                        relationship_result = supabase.table('employee_projects').insert({
                            "employee_id": employee_id,
                            "project_id": project_id,
                            "text_id": result["project_chunk_id"],  # Single text_id referencing project chunk only
                            "role": employee_role  # Use the project-specific role
                        }).execute()
                        
                        if relationship_result.data:
                            relationship_id = relationship_result.data[0].get('id', None)
                            result["employee_project_relationships"].append({
                                "employee_id": employee_id,
                                "project_id": project_id,
                                "relationship_id": relationship_id,
                                "role": employee_role
                            })
                            logger.info(f"Created employee-project relationship between employee {employee_id} and project {project_id} with role '{employee_role}'")
                        else:
                            logger.warning(f"No data returned from employee-project relationship insert for employee {employee_id}")
                    else:
                        logger.warning("Cannot create employee-project relationship: missing project chunk text_id")
                    
                except Exception as e:
                    logger.error(f"Error creating employee-project relationship for employee {employee_id}: {e}")
                    # Continue with other employees
            
            if not matching_employees:
                logger.warning("No matching employees found for the firms in the document")
                
        except Exception as e:
            logger.error(f"Error processing employee-project relationships: {e}")
            # Continue with the rest of the function
        
        logger.info(f"Successfully uploaded document {pdf_name} to Supabase")
        logger.info(f"Created {len(result['employee_project_relationships'])} employee-project relationships")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading to Supabase: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        return result 

def document_exists(pdf_name: str) -> Optional[str]:
    """
    Check if a document with the given name already exists in the database
    
    Args:
        pdf_name: Name of the PDF file
        
    Returns:
        Document ID if exists, None otherwise
    """
    if not supabase:
        logger.warning("Supabase client not available, cannot check if document exists")
        return None
    
    try:
        # Query the documents table for documents with matching pdf_name
        result = supabase.table('documents').select('id, pdf_name, document_link').eq('pdf_name', pdf_name).execute()
        
        if result.data and len(result.data) > 0:
            document_id = result.data[0]['id']
            document_link = result.data[0]['document_link']
            logger.info(f"Document '{pdf_name}' already exists with ID: {document_id}")
            logger.info(f"Document link: {document_link}")
            return document_id
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking if document exists: {e}")
        return None


def process_project_pdf(pdf_path: str, use_mistral: bool = False) -> Dict[str, Any]:
    """
    Main function to process a project PDF file
    
    Args:
        pdf_path: Path to the PDF file
        use_mistral: Whether to try using Mistral AI before OpenAI
        
    Returns:
        Dictionary with processing status and result details
    """
    try:
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        
        pdf_name = os.path.basename(pdf_path)
        
        # Check if document already exists
        existing_document_id = document_exists(pdf_name)
        if existing_document_id:
            return {
                "status": "exists",
                "message": f"Document '{pdf_name}' already exists in the database with ID: {existing_document_id}",
                "document_id": existing_document_id
            }
            
        # Basic environment verification (without bucket check)
        if not verify_environment(skip_bucket_check=True):
            error_msg = "Environment not properly configured - see log for details"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
            
        # 1. Extract text from PDF
        logger.info(f"Extracting text from {os.path.basename(pdf_path)}")
        extracted_text = extract_text_from_pdf(pdf_path)
        
        if not extracted_text or len(extracted_text.strip()) < 100:
            error_msg = f"Failed to extract meaningful text from {os.path.basename(pdf_path)}. Extracted only {len(extracted_text)} characters."
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 2. Extract project and firms chunks
        logger.info("Extracting project and firms chunks")
        chunks = extract_project_and_firms_chunks(extracted_text)
        
        if not chunks["project_chunk"] or not chunks["firms_chunk"]:
            error_msg = "Failed to extract required chunks from the PDF"
            logger.error(error_msg)
            if not chunks["project_chunk"]:
                logger.error("Missing project chunk")
            if not chunks["firms_chunk"]:
                logger.error("Missing firms chunk")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 3. Process chunks with AI
        logger.info("Processing extracted chunks with AI")
        try:
            structured_data = process_with_ai(chunks, use_mistral)
        except Exception as e:
            error_msg = f"AI processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Verify we have project and firms data
        if not structured_data.get("project") or not structured_data.get("firms"):
            error_msg = "AI processing did not extract required project or firms data"
            logger.error(error_msg)
            if not structured_data.get("project"):
                logger.error("Missing project data")
            if not structured_data.get("firms"):
                logger.error("Missing firms data")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 4. Upload to Supabase
        logger.info("Uploading processed data to Supabase")
        try:
            result = upload_to_supabase(pdf_path, chunks, structured_data)
        except Exception as e:
            error_msg = f"Supabase upload failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error", 
                "message": error_msg
            }
        
        # Check if upload was successful
        if result.get("status") == "error":
            error_msg = f"Supabase upload failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        
        return {
            "status": "success",
            "message": f"Successfully processed {os.path.basename(pdf_path)}",
            "result": result
        }
        
    except FileNotFoundError as e:
        logger.error(str(e))
        return {
            "status": "error",
            "message": str(e)
        }
    except EnvironmentError as e:
        logger.error(str(e))
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return {
            "status": "error",
            "message": f"Failed to process {os.path.basename(pdf_path)}: {str(e)}"
        }


def main():
    """
    Main entry point for the script when run directly
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process project PDF files and upload to Supabase")
    parser.add_argument("pdf_path", help="Path to the project PDF file to process")
    parser.add_argument("--skip-verify", action="store_true", help="Skip environment verification")
    parser.add_argument("--use-mistral", action="store_true", help="Try using Mistral AI before OpenAI")
    parser.add_argument("--force", action="store_true", help="Force processing even if document already exists")
    args = parser.parse_args()
    
    # Verify PDF file exists
    if not os.path.exists(args.pdf_path):
        logger.error(f"PDF file not found: {args.pdf_path}")
        logger.error("Please provide a valid path to a PDF file")
        sys.exit(1)
    
    # Run environment verification if not skipped
    if not args.skip_verify:
        logger.info("Verifying environment...")
        if not verify_environment(skip_bucket_check=False):
            logger.error("Environment not properly configured. Please check error messages above.")
            
            # Guide user on next steps
            if not supabase:
                logger.error("Supabase setup guide:")
                logger.error("1. Ensure SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY are in your .env file")
                logger.error("2. Use your Supabase project URL (e.g., https://your-project.supabase.co)")
                logger.error("3. Use your private API key from Supabase project settings")
            
            if not openai_client:
                logger.error("OpenAI API setup guide:")
                logger.error("1. Visit https://platform.openai.com/api-keys to get your API key")
                logger.error("2. Make sure your OPENAI_API_KEY in .env is correct and not expired")
                logger.error("3. Set OPENAI_MODEL in your .env file (default is gpt-4o)")
            
            if supabase and DOCUMENTS_BUCKET:
                logger.error("Supabase Storage setup guide:")
                logger.error(f"1. Create a bucket named '{DOCUMENTS_BUCKET}' in Supabase Storage")
                logger.error("2. Ensure your service key has permission to access and modify storage")
                logger.error("3. Consider adding the following RLS policy for storage:")
                logger.error("   (bucketid = 'documents'::text) AND (auth.role() = 'service_role'::text)")
            
            sys.exit(1)
        
        logger.info("Environment verification passed")
    
    # Check if document already exists (only if not forcing processing)
    if not args.force:
        pdf_name = os.path.basename(args.pdf_path)
        existing_document_id = document_exists(pdf_name)
        if existing_document_id:
            logger.info(f"Document '{pdf_name}' already exists with ID: {existing_document_id}")
            logger.info("To force processing, use the --force flag")
            sys.exit(0)
    
    logger.info(f"Processing project PDF file: {args.pdf_path}")
    result = process_project_pdf(args.pdf_path, use_mistral=args.use_mistral)
    
    if result["status"] == "success":
        logger.info(result["message"])
        logger.info(f"Document ID: {result.get('result', {}).get('document_id')}")
        logger.info(f"Project ID: {result.get('result', {}).get('project_id')}")
        logger.info(f"Matching employees found: {len(result.get('result', {}).get('matching_employee_ids', []))}")
        logger.info(f"Employee-project relationships created: {len(result.get('result', {}).get('employee_project_relationships', []))}")
        sys.exit(0)
    elif result["status"] == "exists":
        logger.info(result["message"])
        logger.info("To force processing, use the --force flag")
        sys.exit(0)
    else:
        logger.error(result["message"])
        sys.exit(1)


if __name__ == "__main__":
    main() 
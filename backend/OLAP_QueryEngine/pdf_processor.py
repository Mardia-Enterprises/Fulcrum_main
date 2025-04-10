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
    logger = logging.getLogger("pdf_processor")
    logger.info("Mistral client successfully imported")
except ImportError as e:
    logger = logging.getLogger("pdf_processor")
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
logger = logging.getLogger("pdf_processor")

# Load environment variables
load_dotenv()

# Configure Supabase client with updated environment variable names
supabase_url = os.getenv("SUPABASE_PROJECT_URL")  # Updated variable name
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")  # Using private key for server operations
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

# OpenAI is optional as fallback
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OpenAI API key not found in .env file")
    logger.warning("OpenAI will not be available as a fallback")
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
            logger.warning(f"Failed to connect to OpenAI API: {e}")
            logger.warning("OpenAI will not be available as a fallback")
            openai_client = None
            
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI client: {e}")
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
    
    # OpenAI is required (Mistral is optional)
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
            # First get the column information
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


def process_with_ai(text: str, use_mistral: bool = False) -> Dict[str, Any]:
    """
    Process the extracted text using OpenAI by default, with optional Mistral
    
    Args:
        text: Extracted text from PDF
        use_mistral: Whether to try using Mistral first (default: False)
        
    Returns:
        Structured data containing team and project information
    """
    logger.info("Processing extracted text with AI")
    
    system_prompt = """
    You are an expert at extracting structured information from resume-like documents.
    Extract the following information from the provided document:
    
    1. Team/Employee information: 
       - name: The full name of the person
       - role: Their job title or position
    
    2. Project information (there may be multiple projects):
       - name: The name of each project
       - location: The location of each project
    
    Return the information as a JSON object with the following structure:
    {
        "team": {
            "name": "Person Name",
            "role": "Person Role"
        },
        "team_chunk": {
            "text": "Full text of the team/employee section"
        },
        "projects": [
            {
                "name": "Project 1 Name",
                "location": "Project 1 Location"
            },
            {
                "name": "Project 2 Name",
                "location": "Project 2 Location"
            }
        ],
        "project_chunks": [
            {
                "project_index": 0,
                "text": "Full text of project 1"
            },
            {
                "project_index": 1,
                "text": "Full text of project 2"
            }
        ]
    }
    
    Ensure each project has its complete text in the project_chunks array.
    Make sure to extract the correct location for each project.
    Also ensure the team_chunk contains the full text of the employee/team section.
    """
    
    # Try with Mistral if available and requested
    if use_mistral and mistral_client:
        try:
            logger.info("Attempting to process with Mistral AI")
            
            # Create messages for mistralai
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
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
                    {"role": "user", "content": text}
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


def upload_to_supabase(
    pdf_path: str, 
    structured_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Upload original PDF and processed data to Supabase
    
    Args:
        pdf_path: Path to the PDF file
        structured_data: Processed data from AI
        
    Returns:
        Dictionary with status and IDs of created resources
    """
    if not supabase:
        error_msg = "Supabase client not available, cannot upload data"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    logger.info(f"Uploading PDF and processed data to Supabase: {pdf_path}")
    
    result = {
        "status": "success",
        "document_id": None,
        "team_id": None,
        "team_chunk_id": None,
        "project_ids": [],
        "sharded_document_ids": []
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
            supabase_project_url = os.getenv("SUPABASE_PROJECT_URL")  # Use updated variable name
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
        
        # 3. Insert team data
        try:
            team_data = structured_data.get("team", {})
            team_text = f"Name: {team_data.get('name', '')}\nRole: {team_data.get('role', '')}"
            team_embedding = generate_embeddings(team_text)
            
            team_result = supabase.table('employee').insert({
                "name": team_data.get("name"),
                "role": team_data.get("role"),
                "embedding": team_embedding
            }).execute()
            
            if not team_result.data:
                raise RuntimeError("No data returned from employee insert")
                
            team_id = team_result.data[0]['id']
            result["team_id"] = team_id
        
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting employee: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the employee table")
                raise RuntimeError("Supabase RLS policy error inserting employee - please check your Supabase policies")
            else:
                logger.error(f"Error inserting employee record: {e}")
                raise
        
        # 4. Link team to document
        try:
            # First ensure we have a team chunk created
            team_chunk = structured_data.get("team_chunk", {})
            if team_chunk and "text" in team_chunk:
                team_chunk_text = team_chunk.get("text", "")
                chunk_embedding = generate_embeddings(team_chunk_text)
                
                team_chunk_result = supabase.table('sharded_documents').insert({
                    "document_id": document_id,
                    "text": team_chunk_text,
                    "embedding": chunk_embedding
                }).execute()
                
                if team_chunk_result.data:
                    team_chunk_id = team_chunk_result.data[0]['text_id']
                    result["team_chunk_id"] = team_chunk_id
                    result["sharded_document_ids"].append(team_chunk_id)
                    
                    # Now link team to document using the team_chunk_id (from sharded_documents)
                    supabase.table('employee_documents').insert({
                        "employee_id": team_id,
                        "text_id": team_chunk_id  # Use text_id from sharded_documents, not document_id
                    }).execute()
                    
                    logger.info("Successfully stored team chunk in sharded_documents and linked to employee")
                else:
                    logger.warning("Team chunk insert returned no data")
            else:
                logger.warning("No team chunk data found in the processed data")
                
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                logger.error(f"RLS policy error inserting team chunk or linking employee to document: {e}")
                logger.error("Please ensure your Supabase service key has RLS policies enabled for the sharded_documents and employee_documents tables")
            else:
                logger.error(f"Error inserting team chunk or linking employee to document: {e}")
            # Continue anyway as sharded documents are supplementary
        
        # 5. Process projects
        for i, project in enumerate(structured_data.get("projects", [])):
            try:
                # Insert project
                project_result = supabase.table('projects').insert({
                    "name": project.get("name"),
                    "location": project.get("location")
                }).execute()
                
                if not project_result.data:
                    logger.warning(f"No data returned from project insert for project {i}")
                    continue
                    
                project_id = project_result.data[0]['id']
                result["project_ids"].append(project_id)
                
                # Find the related project chunk
                project_chunk = next(
                    (chunk for chunk in structured_data.get("project_chunks", []) 
                     if chunk.get("project_index") == i),
                    None
                )
                
                if project_chunk:
                    try:
                        # Insert sharded document
                        chunk_text = project_chunk.get("text", "")
                        chunk_embedding = generate_embeddings(chunk_text)
                        
                        shard_result = supabase.table('sharded_documents').insert({
                            "document_id": document_id,
                            "text": chunk_text,
                            "embedding": chunk_embedding
                        }).execute()
                        
                        if shard_result.data:
                            shard_id = shard_result.data[0]['text_id']
                            result["sharded_document_ids"].append(shard_id)
                            
                            # Link project to document using the project chunk text_id
                            supabase.table('project_documents').insert({
                                "project_id": project_id,
                                "text_id": shard_id  # Use text_id from sharded_documents
                            }).execute()
                            
                            # Link team to project with project text_id
                            try:
                                # Get employee role
                                employee_role = team_data.get("role", "")
                                
                                # Link team to project with only the project text_id
                                supabase.table('employee_projects').insert({
                                    "employee_id": team_id,
                                    "project_id": project_id,
                                    "text_id": shard_id,  # Single text_id referencing project chunk only
                                    "role": employee_role  # Add role from team data
                                }).execute()
                                logger.info(f"Created employee-project relationship for project {i} with text_id: {shard_id} and role: {employee_role}")
                            except Exception as e:
                                logger.error(f"Error creating employee-project relationship: {e}")
                                logger.error("Check your employee_projects table schema structure")
                        else:
                            logger.warning(f"No data returned from shard insert for project {i}")
                        
                    except Exception as e:
                        if "row-level security policy" in str(e).lower():
                            logger.error(f"RLS policy error with project chunk {i}: {e}")
                        else:
                            logger.error(f"Error processing project chunk {i}: {e}")
                        # Continue with other projects
                else:
                    logger.warning(f"No project chunk found for project {i}")
                
            except Exception as e:
                if "row-level security policy" in str(e).lower():
                    logger.error(f"RLS policy error with project {i}: {e}")
                else:
                    logger.error(f"Error processing project {i}: {e}")
                # Continue with other projects
        
        logger.info(f"Successfully uploaded document {pdf_name} to Supabase")
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


def process_pdf(pdf_path: str, use_mistral: bool = False) -> Dict[str, Any]:
    """
    Main function to process a PDF file
    
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
        
        # 2. Process text with AI
        logger.info(f"Processing extracted text ({len(extracted_text)} characters) with AI")
        try:
            structured_data = process_with_ai(extracted_text, use_mistral)
        except Exception as e:
            error_msg = f"AI processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
        
        # Verify we have team and project data
        if not structured_data.get("team") or not structured_data.get("projects"):
            error_msg = "AI processing did not extract required team or project data"
            logger.error(error_msg)
            if not structured_data.get("team"):
                logger.error("Missing team data")
            if not structured_data.get("projects"):
                logger.error("Missing project data")
            return {
                "status": "error",
                "message": error_msg
            }
        
        # 3. Upload to Supabase
        logger.info("Uploading processed data to Supabase")
        try:
            result = upload_to_supabase(pdf_path, structured_data)
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


def check_sample_files():
    """
    Check if the sample files mentioned in the requirements exist
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    sample_files = [
        "Mark-Wingate-1.pdf",
        "Mark-Wingate-sections.pdf"
    ]
    
    missing_files = []
    
    for file in sample_files:
        file_path = os.path.join(root_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        logger.warning(f"Required PDF files not found: {', '.join(missing_files)}")


def main():
    """
    Main entry point for the script when run directly
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process PDF files and upload to Supabase")
    parser.add_argument("pdf_path", help="Path to the PDF file to process")
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
        
    logger.info(f"Processing PDF file: {args.pdf_path}")
    result = process_pdf(args.pdf_path, use_mistral=args.use_mistral)
    
    if result["status"] == "success":
        logger.info(result["message"])
        logger.info(f"Document ID: {result.get('result', {}).get('document_id')}")
        logger.info(f"Team ID: {result.get('result', {}).get('team_id')}")
        logger.info(f"Projects added: {len(result.get('result', {}).get('project_ids', []))}")
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
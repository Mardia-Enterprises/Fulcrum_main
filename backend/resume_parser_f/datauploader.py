#!/usr/bin/env python3
"""
Module for uploading extracted Section F project data to Supabase,
including generating embeddings with OpenAI.
"""

import os
import sys
import json
import time
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

# Check for OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("\033[91mError: OPENAI_API_KEY not found in .env file\033[0m")
    logger.error("Please add your OpenAI API key to the .env file in the root directory")
    sys.exit(1)

# Check for Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("SUPABASE_PRIVATE_API_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("\033[91mError: Supabase credentials not found in .env file\033[0m")
    logger.error("Please add your Supabase URL and API key to the .env file in the root directory")
    sys.exit(1)

# Initialize OpenAI client
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("\033[92m✓ OpenAI client initialized\033[0m")
except ImportError:
    logger.error("\033[91mError: Failed to import OpenAI. Please install with 'pip install openai'\033[0m")
    sys.exit(1)
except Exception as e:
    logger.error(f"\033[91mError initializing OpenAI client: {str(e)}\033[0m")
    sys.exit(1)

# Initialize Supabase client
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("\033[92m✓ Supabase client initialized\033[0m")
except ImportError:
    logger.error("\033[91mError: Failed to import Supabase. Please install with 'pip install supabase'\033[0m")
    sys.exit(1)
except Exception as e:
    logger.error(f"\033[91mError initializing Supabase client: {str(e)}\033[0m")
    sys.exit(1)

def project_to_text(project_data: Dict[str, Any]) -> str:
    """
    Convert a project data dictionary to a text string for embedding.
    
    Args:
        project_data: Project data dictionary with fields like title_and_location, etc.
        
    Returns:
        Text representation of the project data
    """
    text_parts = []
    
    # Add title and location
    if "title_and_location" in project_data:
        text_parts.append(f"Project: {project_data['title_and_location']}")
    
    # Add project owner
    if "project_owner" in project_data:
        text_parts.append(f"Owner: {project_data['project_owner']}")
    
    # Add year completed
    if "year_completed" in project_data:
        year_info = project_data["year_completed"]
        if isinstance(year_info, dict):
            prof_year = year_info.get("professional_services")
            const_year = year_info.get("construction")
            
            if prof_year:
                text_parts.append(f"Professional services completed: {prof_year}")
            if const_year:
                text_parts.append(f"Construction completed: {const_year}")
    
    # Add points of contact
    if "point_of_contact_name" in project_data:
        text_parts.append(f"Contact: {project_data['point_of_contact_name']}")
    
    # Add brief description
    if "brief_description" in project_data:
        text_parts.append(f"Description: {project_data['brief_description']}")
    
    # Add firms from section C
    if "firms_from_section_c" in project_data and isinstance(project_data["firms_from_section_c"], list):
        firms = project_data["firms_from_section_c"]
        if firms:
            text_parts.append("Project team:")
            for firm in firms:
                if isinstance(firm, dict):
                    firm_name = firm.get("firm_name", "Unknown")
                    firm_loc = firm.get("firm_location", "Unknown")
                    firm_role = firm.get("role", "Unknown")
                    text_parts.append(f"  {firm_name} ({firm_loc}) - {firm_role}")
    
    # Join all parts with newlines
    return "\n".join(text_parts)

def generate_embedding(text: str, max_retries: int = 3, base_delay: float = 1.0) -> Optional[List[float]]:
    """
    Generate an embedding for the given text using OpenAI.
    Uses exponential backoff for retries.
    
    Args:
        text: Text to embed
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        
    Returns:
        Embedding as a list of floats, or None if embedding failed
    """
    if not text:
        logger.error("\033[91mError: No text provided for embedding\033[0m")
        return None
    
    logger.info("Generating embedding with OpenAI...")
    
    # Retry with exponential backoff
    attempt = 0
    while attempt < max_retries:
        try:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))
            
            if attempt > 1:
                logger.info(f"Retry attempt {attempt}/{max_retries} (delay: {delay:.2f}s)...")
                time.sleep(delay)
            
            # Make the API call
            response = openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            
            # Extract the embedding
            embedding = response.data[0].embedding
            
            # Log the embedding dimensions
            embedding_length = len(embedding)
            logger.info(f"\033[92m✓ Generated embedding with {embedding_length} dimensions\033[0m")
            
            # Check if we have the correct dimensions for pgvector (should be 1536)
            if embedding_length != 1536:
                logger.warning(f"\033[93mWarning: Embedding has {embedding_length} dimensions, expected 1536\033[0m")
            
            return embedding
            
        except Exception as e:
            logger.error(f"\033[91mError generating embedding: {str(e)}\033[0m")
            if attempt < max_retries:
                logger.info(f"Waiting {delay:.2f}s before retrying...")
                time.sleep(delay)
            else:
                logger.error("\033[91mExceeded maximum retries. Embedding generation failed.\033[0m")
                return None
    
    return None

def verify_supabase_connection() -> bool:
    """
    Verify that the Supabase connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    logger.info("Verifying Supabase connection...")
    
    try:
        # Try to query the projects table
        result = supabase.table('projects').select('id').limit(1).execute()
        logger.info("\033[92m✓ Supabase connection verified\033[0m")
        return True
    except Exception as e:
        logger.error(f"\033[91mError connecting to Supabase: {str(e)}\033[0m")
        return False

def upsert_project_in_supabase(
    project_id: str, 
    title: str, 
    project_data: Dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> bool:
    """
    Upsert a project into the Supabase projects table.
    
    Args:
        project_id: Unique identifier for the project
        title: Project title for display
        project_data: Complete project data dictionary
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        
    Returns:
        True if upsert was successful, False otherwise
    """
    if not project_id or not project_data:
        logger.error("\033[91mError: Missing project ID or data\033[0m")
        return False
    
    logger.info(f"Upserting project to Supabase: {project_id}")
    
    # Check if the project already exists to merge data
    try:
        existing_data = None
        existing_result = supabase.table('projects').select('project_data').eq('id', project_id).execute()
        
        if existing_result.data and len(existing_result.data) > 0:
            existing_data = existing_result.data[0].get('project_data')
            logger.info(f"Found existing project data with ID {project_id}")
            
            # Merge the existing data with the new data, giving preference to non-empty new values
            if existing_data:
                for key, value in existing_data.items():
                    # Only use existing data if the new data doesn't have this field or has an empty value
                    if key not in project_data or not project_data[key]:
                        project_data[key] = value
                
                logger.info("Merged existing data with new data")
    except Exception as e:
        logger.warning(f"Could not check for existing project data: {str(e)}")
    
    # Generate text for embedding
    project_text = project_to_text(project_data)
    
    # Generate embedding
    embedding = generate_embedding(project_text)
    if not embedding:
        logger.error("\033[91mFailed to generate embedding, cannot upsert to Supabase\033[0m")
        return False
    
    # Prepare data for Supabase
    supabase_data = {
        "id": project_id,
        "title": title,
        "project_data": project_data,
        "embedding": embedding
    }
    
    # Retry with exponential backoff
    attempt = 0
    while attempt < max_retries:
        try:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))
            
            if attempt > 1:
                logger.info(f"Retry attempt {attempt}/{max_retries} (delay: {delay:.2f}s)...")
                time.sleep(delay)
            
            # Upsert to Supabase
            result = supabase.table('projects').upsert(supabase_data).execute()
            
            # Check for errors
            if hasattr(result, 'error') and result.error:
                raise Exception(f"Supabase error: {result.error}")
            
            logger.info(f"\033[92m✓ Successfully upserted project to Supabase: {project_id}\033[0m")
            return True
            
        except Exception as e:
            logger.error(f"\033[91mError upserting to Supabase: {str(e)}\033[0m")
            if attempt < max_retries:
                logger.info(f"Waiting {delay:.2f}s before retrying...")
                time.sleep(delay)
            else:
                logger.error("\033[91mExceeded maximum retries. Upsert failed.\033[0m")
                return False
    
    return False

def normalize_title(title: str) -> str:
    """
    Normalize a title for comparison to detect duplicates.
    
    Args:
        title: Project title
        
    Returns:
        Normalized title for comparison
    """
    if not isinstance(title, str):
        title = str(title)
    return title.lower().replace(" ", "").replace(",", "").replace(".", "").replace("-", "").replace("_", "")

def is_duplicate_project(title: str) -> Optional[str]:
    """
    Check if a project with a similar title already exists in Supabase.
    
    Args:
        title: Project title to check
        
    Returns:
        The ID of the existing project if found, None otherwise
    """
    if not title:
        return None
        
    try:
        # Get all projects from Supabase
        result = supabase.table('projects').select('id, title').execute()
        
        if not result.data:
            return None
            
        # Normalize the title for comparison
        normalized_title = normalize_title(title)
        
        # Check for similar titles
        for project in result.data:
            existing_title = project.get('title', '')
            if not existing_title:
                continue
                
            existing_normalized = normalize_title(existing_title)
            
            # If the normalized titles are similar enough, consider it a duplicate
            if normalized_title in existing_normalized or existing_normalized in normalized_title:
                return project.get('id')
                
        return None
    except Exception as e:
        logger.error(f"\033[91mError checking for duplicate project: {str(e)}\033[0m")
        return None

def process_json_files(
    json_dir: Union[str, Path], 
    limit: Optional[int] = None
) -> int:
    """
    Process all JSON files in a directory and upsert them to Supabase.
    
    Args:
        json_dir: Directory containing JSON files
        limit: Maximum number of files to process (None for all)
        
    Returns:
        Number of successfully processed files
    """
    json_dir = Path(json_dir)
    if not json_dir.exists():
        logger.error(f"\033[91mError: JSON directory not found: {json_dir}\033[0m")
        return 0
    
    logger.info(f"\n\033[1;36m===== Processing JSON files in: {json_dir} =====\033[0m")
    
    # Find all JSON files
    json_files = list(json_dir.glob("*.json"))
    if not json_files:
        logger.warning(f"\033[93mNo JSON files found in {json_dir}\033[0m")
        return 0
    
    logger.info(f"Found {len(json_files)} JSON files")
    if limit:
        json_files = json_files[:limit]
        logger.info(f"Processing first {limit} JSON files")
    
    # Verify Supabase connection before processing
    if not verify_supabase_connection():
        logger.error("\033[91mCannot connect to Supabase, aborting processing\033[0m")
        return 0
    
    # Track processed project titles to avoid duplicates within the same batch
    processed_titles = {}
    
    # Process each JSON file
    success_count = 0
    for i, json_file in enumerate(json_files):
        logger.info(f"\nProcessing file {i+1}/{len(json_files)}: {json_file.name}")
        
        try:
            # Load JSON data
            with open(json_file, "r") as f:
                project_data = json.load(f)
            
            # Extract title and create ID
            title = project_data.get("title_and_location", "Unknown Project")
            # Ensure title is a string
            if isinstance(title, dict):
                # If it's a dict, try to convert it to a string representation
                title = str(title.get("title", "")) if "title" in title else str(title)
            elif not isinstance(title, str):
                # If it's any other non-string type, convert to string
                title = str(title)
                
            # Check if this title has already been processed in this batch
            normalized_title = normalize_title(title)
            if normalized_title in processed_titles:
                logger.info(f"\033[93mSkipping duplicate project (already processed in this batch): {title}\033[0m")
                continue
                
            # Check if this project already exists in Supabase
            existing_id = is_duplicate_project(title)
            if existing_id:
                logger.info(f"\033[93mFound existing project with similar title: {title}\033[0m")
                logger.info(f"\033[93mUpdating existing project with ID: {existing_id}\033[0m")
                project_id = existing_id
            else:
                # Create a clean ID from the title or filename
                project_id = json_file.stem
                if project_id.startswith("project_data_"):
                    # Use the title to create a more meaningful ID
                    clean_title = title.lower().replace(" ", "_").replace(",", "").replace(".", "")
                    project_id = f"proj_{clean_title[:30]}_{json_file.stem[-8:]}"
            
            # Upsert to Supabase
            success = upsert_project_in_supabase(project_id, title, project_data)
            
            if success:
                success_count += 1
                # Add to processed titles
                processed_titles[normalized_title] = project_id
                
                # Add a small delay between processing to avoid rate limits
                if i < len(json_files) - 1:
                    time.sleep(1)
        except Exception as e:
            logger.error(f"\033[91mError processing {json_file.name}: {str(e)}\033[0m")
            logger.error(traceback.format_exc())
    
    logger.info(f"\n\033[1;36m===== Processing Summary =====\033[0m")
    logger.info(f"Total JSON files: {len(json_files)}")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {len(json_files) - success_count}")
    logger.info(f"Unique projects: {len(processed_titles)}")
    
    return success_count

if __name__ == "__main__":
    # If run directly, process JSON files in the specified directory
    if len(sys.argv) > 1:
        json_dir = sys.argv[1]
    else:
        # Default to output directory in the same folder
        json_dir = script_dir / "output"
    
    logger.info(f"Processing JSON files in {json_dir}")
    count = process_json_files(json_dir)
    logger.info(f"Processed {count} JSON files successfully") 
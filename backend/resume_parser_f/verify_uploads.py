#!/usr/bin/env python3
"""
Script to verify that projects have been properly uploaded to Supabase.
This script checks the projects table and displays information about the uploaded projects.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - \033[1;33m%(levelname)s\033[0m - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

def verify_table_structure() -> bool:
    """
    Verify that the projects table exists and has the correct structure.
    
    Returns:
        True if the table structure is correct, False otherwise
    """
    logger.info("\n\033[1;36m===== Verifying Table Structure =====\033[0m")
    
    # Import Supabase client
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_PROJECT_URL")
        supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("\033[91mError: Supabase credentials not found\033[0m")
            return False
        
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Try to query a single row to check if table exists
        logger.info("Checking if projects table exists...")
        result = supabase.table('projects').select('*').limit(1).execute()
        
        # Check if we got a valid response
        if hasattr(result, 'data'):
            logger.info("\033[92m✓ Table 'projects' exists\033[0m")
            
            # If we have data, check the structure
            if result.data:
                sample = result.data[0]
                logger.info("\033[92m✓ Found project record\033[0m")
                
                # Check for required fields
                required_fields = ['id', 'title', 'project_data', 'embedding']
                missing_fields = [field for field in required_fields if field not in sample]
                
                if missing_fields:
                    logger.error(f"\033[91mError: Missing fields in table: {missing_fields}\033[0m")
                    return False
                
                logger.info("\033[92m✓ Table has all required fields\033[0m")
                return True
            else:
                logger.warning("\033[93mWarning: Table exists but is empty\033[0m")
                
                # Try a test insertion to check the structure
                logger.info("Attempting test insertion to verify table structure...")
                test_data = {
                    'id': 'test_verify_structure',
                    'title': 'Test Project',
                    'project_data': {
                        'title_and_location': 'Test Project, Test Location',
                        'project_owner': 'Test Owner'
                    },
                    'embedding': [0.1] * 1536  # 1536 dimensions
                }
                
                try:
                    test_result = supabase.table('projects').insert(test_data).execute()
                    logger.info("\033[92m✓ Test insertion successful\033[0m")
                    
                    # Clean up test data
                    supabase.table('projects').delete().eq('id', 'test_verify_structure').execute()
                    logger.info("Test data cleaned up")
                    
                    return True
                except Exception as e:
                    logger.error(f"\033[91mError: Test insertion failed: {str(e)}\033[0m")
                    logger.error("This suggests the table structure is not correct")
                    return False
        else:
            logger.error("\033[91mError: Failed to query projects table\033[0m")
            return False
            
    except Exception as e:
        logger.error(f"\033[91mError verifying table structure: {str(e)}\033[0m")
        return False

def check_permissions() -> bool:
    """
    Check if the current credentials have permission to write to the projects table.
    
    Returns:
        True if permissions are correct, False otherwise
    """
    logger.info("\n\033[1;36m===== Checking Permissions =====\033[0m")
    
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        # Try a simple insert operation
        logger.info("Testing insert permission...")
        test_id = f"permission_test_{os.urandom(4).hex()}"
        test_data = {
            'id': test_id,
            'title': 'Permission Test',
            'project_data': {'test': True},
            'embedding': [0.1] * 1536
        }
        
        result = supabase.table('projects').insert(test_data).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"\033[91mError: Insert permission denied: {result.error}\033[0m")
            return False
        
        logger.info("\033[92m✓ Insert permission confirmed\033[0m")
        
        # Try to delete the test record
        logger.info("Testing delete permission...")
        delete_result = supabase.table('projects').delete().eq('id', test_id).execute()
        
        if hasattr(delete_result, 'error') and delete_result.error:
            logger.error(f"\033[91mError: Delete permission denied: {delete_result.error}\033[0m")
            return False
        
        logger.info("\033[92m✓ Delete permission confirmed\033[0m")
        return True
        
    except Exception as e:
        logger.error(f"\033[91mError checking permissions: {str(e)}\033[0m")
        return False

def test_sample_upload() -> bool:
    """
    Test uploading a sample project to confirm the upload process works.
    
    Returns:
        True if the upload was successful, False otherwise
    """
    logger.info("\n\033[1;36m===== Testing Sample Upload =====\033[0m")
    
    try:
        # Import the required function
        sys.path.append(str(script_dir))
        from datauploader import upsert_project_in_supabase
        
        # Sample project data based on the provided JSON structure
        sample_project = {
            "project_owner": "TEST OWNER",
            "year_completed": {"professional_services": 2023, "construction": None},
            "point_of_contact": "555-555-5555",
            "brief_description": "This is a test project for upload verification.",
            "title_and_location": "Test Project Upload, Test Location",
            "firms_from_section_c": [
                {"role": "Prime", "firm_name": "Test Firm", "firm_location": "Test City, ST"}
            ],
            "point_of_contact_name": "Test Contact"
        }
        
        # Use a unique ID for the test
        test_id = f"verify_test_{os.urandom(4).hex()}"
        title = sample_project["title_and_location"]
        
        # Try to upload
        logger.info(f"Uploading test project with ID: {test_id}")
        success = upsert_project_in_supabase(test_id, title, sample_project)
        
        if not success:
            logger.error("\033[91mFailed to upload test project\033[0m")
            return False
        
        logger.info("\033[92m✓ Test project uploaded successfully\033[0m")
        
        # Verify it exists in the database
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        result = supabase.table('projects').select('*').eq('id', test_id).execute()
        
        if not result.data or len(result.data) == 0:
            logger.error("\033[91mError: Uploaded project not found in database\033[0m")
            return False
        
        logger.info("\033[92m✓ Project found in database\033[0m")
        
        # Check if the embedding was generated correctly
        project = result.data[0]
        has_embedding = 'embedding' in project and project['embedding'] is not None
        
        if not has_embedding:
            logger.error("\033[91mError: Project missing embedding\033[0m")
            return False
        
        embedding_length = len(project['embedding']) if has_embedding else 0
        logger.info(f"\033[92m✓ Embedding generated with {embedding_length} dimensions\033[0m")
        
        # Clean up
        logger.info("Cleaning up test project...")
        supabase.table('projects').delete().eq('id', test_id).execute()
        logger.info("\033[92m✓ Test project cleaned up\033[0m")
        
        return True
        
    except Exception as e:
        logger.error(f"\033[91mError testing sample upload: {str(e)}\033[0m")
        return False

def check_pdf_processing() -> bool:
    """
    Check if any PDFs have been processed and if corresponding JSON files exist.
    
    Returns:
        True if PDFs have been processed, False otherwise
    """
    logger.info("\n\033[1;36m===== Checking PDF Processing =====\033[0m")
    
    # Check for PDF files
    pdf_dir = script_dir.parent / "Section F Resumes"
    if not pdf_dir.exists():
        logger.warning(f"\033[93mPDF directory not found: {pdf_dir}\033[0m")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"\033[93mNo PDF files found in {pdf_dir}\033[0m")
        return False
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Check for JSON output
    output_dir = script_dir / "output"
    if not output_dir.exists():
        logger.warning(f"\033[93mOutput directory not found: {output_dir}\033[0m")
        return False
    
    json_files = list(output_dir.glob("*.json"))
    if not json_files:
        logger.warning(f"\033[93mNo JSON files found in {output_dir}\033[0m")
        return False
    
    logger.info(f"Found {len(json_files)} JSON files")
    
    # Check one of the JSON files to see if it has the required fields
    if json_files:
        try:
            with open(json_files[0], 'r') as f:
                data = json.load(f)
            
            required_fields = [
                "title_and_location",
                "year_completed",
                "project_owner",
                "point_of_contact_name",
                "point_of_contact",
                "brief_description",
                "firms_from_section_c"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                logger.warning(f"\033[93mWarning: JSON file missing required fields: {missing_fields}\033[0m")
            else:
                logger.info("\033[92m✓ JSON file has all required fields\033[0m")
                
            return True
        except Exception as e:
            logger.error(f"\033[91mError checking JSON file: {str(e)}\033[0m")
            return False
    
    return False

def count_projects() -> int:
    """
    Count the number of projects in the Supabase database.
    
    Returns:
        Number of projects in the database
    """
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        result = supabase.table('projects').select('id').execute()
        
        if hasattr(result, 'data'):
            return len(result.data)
        else:
            return 0
    except Exception as e:
        logger.error(f"\033[91mError counting projects: {str(e)}\033[0m")
        return 0

def display_projects(limit: int = 10) -> None:
    """
    Display a list of projects in the Supabase database.
    
    Args:
        limit: Maximum number of projects to display
    """
    logger.info(f"\n\033[1;36m===== Projects in Supabase (limit {limit}) =====\033[0m")
    
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        result = supabase.table('projects').select('id, title, project_data->>project_owner').limit(limit).execute()
        
        if not hasattr(result, 'data') or not result.data:
            logger.warning("\033[93mNo projects found in database\033[0m")
            return
        
        logger.info(f"Found {len(result.data)} projects:")
        
        for i, project in enumerate(result.data, 1):
            project_id = project.get('id', 'unknown')
            title = project.get('title', 'Unknown Title')
            owner = project.get('project_owner', 'Unknown Owner')
            
            logger.info(f"{i}. {title}")
            logger.info(f"   ID: {project_id}")
            logger.info(f"   Owner: {owner}")
            logger.info("")
            
    except Exception as e:
        logger.error(f"\033[91mError displaying projects: {str(e)}\033[0m")

def test_search() -> bool:
    """
    Test the semantic search functionality.
    
    Returns:
        True if search is working, False otherwise
    """
    logger.info("\n\033[1;36m===== Testing Semantic Search =====\033[0m")
    
    try:
        from supabase import create_client
        from openai import OpenAI
        
        # Initialize clients
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Generate embedding for search query
        logger.info("Generating embedding for test search query...")
        search_query = "USACE projects"
        
        response = openai_client.embeddings.create(
            input=search_query,
            model="text-embedding-3-small"
        )
        
        embedding = response.data[0].embedding
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        
        # Search using embedding
        logger.info("Searching for projects matching query...")
        
        # First check if match_projects function exists
        try:
            # Execute the match_projects function
            result = supabase.rpc(
                'match_projects',
                {
                    'query_embedding': embedding,
                    'match_threshold': 0.5,
                    'match_count': 5
                }
            ).execute()
            
            if not hasattr(result, 'data') or not result.data:
                logger.warning("\033[93mNo search results found\033[0m")
                return False
            
            logger.info(f"\033[92m✓ Found {len(result.data)} search results\033[0m")
            
            # Display the results
            for i, project in enumerate(result.data, 1):
                title = project.get('title', 'Unknown Title')
                similarity = project.get('similarity', 0.0)
                logger.info(f"{i}. {title} (Similarity: {similarity:.4f})")
                
            return True
            
        except Exception as e:
            logger.error(f"\033[91mError using match_projects function: {str(e)}\033[0m")
            
            # Fallback to direct vector comparison
            logger.info("Trying direct vector comparison...")
            
            # SQL query to find similar projects
            sql_query = """
            SELECT id, title, 1 - (embedding <=> :embedding) as similarity
            FROM projects
            ORDER BY similarity DESC
            LIMIT 5;
            """
            
            result = supabase.query(sql_query, {'embedding': embedding}).execute()
            
            if not hasattr(result, 'data') or not result.data:
                logger.warning("\033[93mNo search results found with direct query\033[0m")
                return False
            
            logger.info(f"\033[92m✓ Found {len(result.data)} search results with direct query\033[0m")
            
            # Display the results
            for i, project in enumerate(result.data, 1):
                title = project.get('title', 'Unknown Title')
                similarity = project.get('similarity', 0.0)
                logger.info(f"{i}. {title} (Similarity: {similarity:.4f})")
                
            return True
            
    except Exception as e:
        logger.error(f"\033[91mError testing search: {str(e)}\033[0m")
        return False

def main():
    """Main function to run verification checks"""
    logger.info("\033[1;36m===== Supabase Upload Verification =====\033[0m")
    
    # Check environment variables
    logger.info("\n\033[1;36m===== Checking Environment Variables =====\033[0m")
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("\033[91mError: Supabase credentials not found\033[0m")
        return 1
    
    if not openai_api_key:
        logger.error("\033[91mError: OpenAI API key not found\033[0m")
        return 1
    
    logger.info("\033[92m✓ All required environment variables found\033[0m")
    
    # Run verification checks
    table_ok = verify_table_structure()
    if not table_ok:
        logger.error("\033[91mTable structure verification failed\033[0m")
        return 1
    
    permissions_ok = check_permissions()
    if not permissions_ok:
        logger.error("\033[91mPermissions verification failed\033[0m")
        return 1
    
    upload_ok = test_sample_upload()
    if not upload_ok:
        logger.error("\033[91mSample upload failed\033[0m")
        return 1
    
    # Display projects
    total_projects = count_projects()
    logger.info(f"\nFound {total_projects} total projects in the database")
    
    if total_projects > 0:
        display_projects(limit=5)
        
        # Test search functionality
        search_ok = test_search()
        if not search_ok:
            logger.warning("\033[93mSearch functionality verification failed\033[0m")
    else:
        logger.warning("\033[93mNo projects found in database, skipping search test\033[0m")
    
    # Check PDF processing
    check_pdf_processing()
    
    logger.info("\n\033[92m✓ Verification completed\033[0m")
    
    # Provide summary
    logger.info("\n\033[1;36m===== Summary =====\033[0m")
    logger.info(f"Supabase connection: \033[92mOK\033[0m")
    logger.info(f"Table structure: \033[92mOK\033[0m" if table_ok else f"Table structure: \033[91mFAIL\033[0m")
    logger.info(f"Permissions: \033[92mOK\033[0m" if permissions_ok else f"Permissions: \033[91mFAIL\033[0m")
    logger.info(f"Sample upload: \033[92mOK\033[0m" if upload_ok else f"Sample upload: \033[91mFAIL\033[0m")
    logger.info(f"Total projects: {total_projects}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
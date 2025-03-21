#!/usr/bin/env python
"""
Test script to directly test retrieving a project by ID from Supabase
"""
import logging
import json
import sys
import os
from dotenv import load_dotenv
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_script")

def main():
    """Test retrieving a project by ID directly from Supabase"""
    logger.info("=== Testing direct Supabase project retrieval ===")
    
    # Get the project ID from command line argument or use default
    project_id = sys.argv[1] if len(sys.argv) > 1 else "proj_highway_construction_project_42590158"
    
    # Load environment variables from root .env file
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    logger.info(f"Looking up project with ID: {project_id}")
    
    try:
        # Query all project IDs first to check if the ID exists
        logger.info("Getting all project IDs to check if target exists...")
        all_projects = supabase.table('projects').select('id').execute()
        
        if hasattr(all_projects, 'data'):
            project_ids = [p.get('id') for p in all_projects.data]
            logger.info(f"Found {len(project_ids)} projects in the database")
            logger.info(f"Available IDs: {project_ids}")
            
            if project_id in project_ids:
                logger.info(f"Project {project_id} exists in the database")
            else:
                logger.warning(f"Project {project_id} NOT FOUND in the database!")
        
        # Query for the specific project
        logger.info(f"Executing query: supabase.table('projects').select('*').eq('id', '{project_id}')")
        result = supabase.table('projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error from Supabase: {result.error}")
            return 1
        
        if not result.data or len(result.data) == 0:
            logger.error(f"Project with ID '{project_id}' not found")
            return 1
        
        # Print project data
        project = result.data[0]
        logger.info(f"Found project: {project.get('title', 'No title')}")
        
        # Print the full JSON
        print("\nFull project JSON:")
        print(json.dumps(project, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
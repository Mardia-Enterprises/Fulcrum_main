#!/usr/bin/env python
"""
Debug script for retrieving a project by ID from Supabase
This creates a minimal version of the get_project_by_id function
"""
import os
import json
import logging
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("debug")

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


def simple_get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """
    A simplified version of get_project_by_id that just returns the raw project data
    """
    try:
        logger.info(f"=== DEBUG: Retrieving project with ID: {project_id} ===")
        
        # Query Supabase for the project - use exactly the same query as in the main function
        logger.info(f"Executing query: supabase.table('projects').select('id, title, project_data').eq('id', '{project_id}')")
        result = supabase.table('projects').select('id, title, project_data').eq('id', project_id).execute()
        
        # Log the raw results
        logger.info(f"Query returned {len(result.data) if hasattr(result, 'data') else 'unknown'} results")
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching project from Supabase: {result.error}")
            return None
        
        if not result.data or len(result.data) == 0:
            logger.warning(f"Project with ID '{project_id}' not found. Empty result set.")
            # Get all project IDs for comparison
            all_projects = supabase.table('projects').select('id').execute()
            if all_projects.data:
                logger.info(f"Available project IDs: {[p.get('id') for p in all_projects.data]}")
            return None
        
        # Get project data
        project_item = result.data[0]
        logger.info(f"Retrieved project: {json.dumps(project_item)[:500]}")
        
        return project_item
    
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        logger.exception(e)
        return None


def main():
    """Test the simple_get_project_by_id function with hardcoded and user-provided IDs"""
    # Get project ID from command line or use default
    project_id = sys.argv[1] if len(sys.argv) > 1 else "proj_highway_construction_project_42590158"
    
    # First try with the user-provided ID
    logger.info(f"Testing with user-provided ID: {project_id}")
    project = simple_get_project_by_id(project_id)
    
    if project:
        print(f"\nProject with ID '{project_id}' found:")
        print(json.dumps(project, indent=2))
    else:
        print(f"\nNo project found with ID '{project_id}'")
    
    # Get all project IDs and test each one
    try:
        logger.info("\nTesting with all available project IDs")
        all_projects = supabase.table('projects').select('id').execute()
        
        if not all_projects.data:
            logger.warning("No projects found in database")
            return 1
        
        for idx, proj in enumerate(all_projects.data):
            test_id = proj.get('id')
            logger.info(f"\nTesting ID {idx+1}: {test_id}")
            
            project = simple_get_project_by_id(test_id)
            if project:
                print(f"Project with ID '{test_id}' found:")
                print(json.dumps(project, indent=2)[:200] + "...")
            else:
                print(f"No project found with ID '{test_id}'")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
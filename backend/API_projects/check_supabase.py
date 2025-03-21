#!/usr/bin/env python3
"""
Diagnostic script to check Supabase connection and projects table access.
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("supabase_check")

# Add parent directory to path for imports
parent_dir = Path(__file__).resolve().parent
backend_dir = parent_dir.parent
sys.path.append(str(parent_dir))
sys.path.append(str(backend_dir))

# Load environment variables from root .env file
root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}")

def check_supabase_connection():
    """
    Check if we can connect to Supabase and retrieve data from the projects table.
    """
    try:
        from supabase import create_client
        
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_PROJECT_URL")
        supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in environment variables")
            logger.error("Please check that SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY are set in your .env file")
            return False
        
        logger.info(f"Supabase URL: {supabase_url}")
        logger.info(f"API Key: {supabase_key[:5]}...{supabase_key[-5:] if len(supabase_key) > 10 else ''}")
        
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Check if we can list tables
        logger.info("Testing connection by retrieving projects...")
        result = supabase.table('projects').select('id, title').limit(5).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error querying projects table: {result.error}")
            return False
        
        # Check if we got data
        if not result.data:
            logger.warning("Projects table exists but contains no data")
            return True
        
        # Print summary of projects found
        logger.info(f"Success! Found {len(result.data)} projects in the table")
        for i, project in enumerate(result.data[:5]):
            project_id = project.get('id', 'Unknown')
            project_title = project.get('title', 'Unknown')
            logger.info(f"  {i+1}. ID: {project_id}, Title: {project_title}")
        
        # Try to retrieve one project with complete data
        if result.data:
            project_id = result.data[0].get('id')
            logger.info(f"Retrieving complete data for project: {project_id}")
            
            detail_result = supabase.table('projects').select('*').eq('id', project_id).execute()
            
            if hasattr(detail_result, 'error') and detail_result.error:
                logger.error(f"Error retrieving project details: {detail_result.error}")
            elif detail_result.data:
                project_item = detail_result.data[0]
                logger.info(f"Project data structure:")
                for key, value in project_item.items():
                    if key == 'embedding':
                        logger.info(f"  {key}: [Vector with {len(value) if isinstance(value, list) else 'unknown'} dimensions]")
                    elif key == 'project_data':
                        if isinstance(value, dict):
                            logger.info(f"  {key}: {{")
                            for k, v in value.items():
                                logger.info(f"    {k}: {type(v).__name__}")
                            logger.info("  }")
                        else:
                            logger.info(f"  {key}: {type(value).__name__}")
                    else:
                        logger.info(f"  {key}: {value if len(str(value)) < 50 else str(value)[:50] + '...'}") 
        
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\n=== Supabase Connection Check ===\n")
    
    success = check_supabase_connection()
    
    if success:
        print("\n✅ Supabase connection successful!")
        print("The API should be able to retrieve projects from the database.")
    else:
        print("\n❌ Supabase connection failed!")
        print("Please check the logs above for details on the error.")
        print("Make sure your .env file contains valid Supabase credentials.") 
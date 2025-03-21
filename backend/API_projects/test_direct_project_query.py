#!/usr/bin/env python
"""
Direct test for project retrieval by ID
This script skips the API and directly queries Supabase
"""
import os
import json
import logging
import sys
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from supabase import create_client
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("direct_test")

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

def test_project_url(project_id):
    """Test direct URL query to Supabase REST API"""
    try:
        url = f"{supabase_url}/rest/v1/projects?id=eq.{project_id}"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        
        logger.info(f"Making direct HTTP request to: {url}")
        response = requests.get(url, headers=headers)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data length: {len(data)}")
            if data:
                logger.info(f"First record: {json.dumps(data[0])[:200]}...")
            else:
                logger.warning("Empty response data")
            return data
        else:
            logger.error(f"Error response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        logger.exception(e)
        return None

def test_supabase_client(project_id):
    """Test using the Supabase client"""
    try:
        logger.info(f"Using Supabase client to query for project ID: {project_id}")
        
        # List all projects first to see if the ID exists
        logger.info("First, getting all projects:")
        all_result = supabase.table('projects').select('id').execute()
        
        if all_result.data:
            project_ids = [p.get('id') for p in all_result.data]
            logger.info(f"Found {len(project_ids)} projects")
            logger.info(f"Project IDs: {project_ids}")
            
            if project_id in project_ids:
                logger.info(f"Confirmed project ID {project_id} exists in the database")
            else:
                logger.warning(f"Project ID {project_id} NOT FOUND in the database")
        
        # Try querying with exact match
        logger.info(f"Testing query: supabase.table('projects').select('*').eq('id', '{project_id}')")
        result1 = supabase.table('projects').select('*').eq('id', project_id).execute()
        
        logger.info(f"Query 1 result data length: {len(result1.data) if hasattr(result1, 'data') else 'None'}")
        if hasattr(result1, 'data') and result1.data:
            logger.info(f"Query 1 first record ID: {result1.data[0].get('id')}")
        
        # Try different query format
        logger.info(f"Testing alternate query: supabase.table('projects').select('*').filter('id', 'eq', '{project_id}')")
        result2 = supabase.table('projects').select('*').filter('id', 'eq', project_id).execute()
        
        logger.info(f"Query 2 result data length: {len(result2.data) if hasattr(result2, 'data') else 'None'}")
        if hasattr(result2, 'data') and result2.data:
            logger.info(f"Query 2 first record ID: {result2.data[0].get('id')}")
        
        # Try with single quotes
        logger.info(f"Testing with single quotes: supabase.table('projects').select('*').eq('id', '{project_id}')")
        result3 = supabase.table('projects').select('*').eq('id', f'{project_id}').execute()
        
        logger.info(f"Query 3 result data length: {len(result3.data) if hasattr(result3, 'data') else 'None'}")
        if hasattr(result3, 'data') and result3.data:
            logger.info(f"Query 3 first record ID: {result3.data[0].get('id')}")
        
        # Try limiting select fields
        logger.info(f"Testing with limited fields: supabase.table('projects').select('id,title').eq('id', '{project_id}')")
        result4 = supabase.table('projects').select('id,title').eq('id', project_id).execute()
        
        logger.info(f"Query 4 result data length: {len(result4.data) if hasattr(result4, 'data') else 'None'}")
        if hasattr(result4, 'data') and result4.data:
            logger.info(f"Query 4 first record ID: {result4.data[0].get('id')}")
        
        return result1
    
    except Exception as e:
        logger.error(f"Error querying with Supabase client: {str(e)}")
        logger.exception(e)
        return None

def main():
    """Run the direct query tests"""
    project_id = sys.argv[1] if len(sys.argv) > 1 else "proj_highway_construction_project_42590158"
    
    logger.info(f"===== TESTING PROJECT ID: {project_id} =====")
    
    # Test direct URL query
    logger.info("\n\n===== TESTING DIRECT URL QUERY =====")
    data = test_project_url(project_id)
    if data:
        print("\nDirect URL query result:")
        print(json.dumps(data, indent=2)[:500] + "...")
    
    # Test with Supabase client
    logger.info("\n\n===== TESTING SUPABASE CLIENT =====")
    result = test_supabase_client(project_id)
    if result and hasattr(result, 'data') and result.data:
        print("\nSupabase client query result:")
        print(json.dumps(result.data[0], indent=2)[:500] + "...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python
"""
Test script to test the API's project retrieval endpoint
"""
import logging
import json
import sys
import os
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_script")

def main():
    """Test the API's project retrieval endpoint"""
    logger.info("=== Testing API /api/projects/:id endpoint ===")
    
    # Get the project ID from command line argument or use default
    project_id = sys.argv[1] if len(sys.argv) > 1 else "proj_highway_construction_project_42590158"
    
    # API URL
    api_url = f"http://localhost:8001/api/projects/{project_id}"
    logger.info(f"Making request to: {api_url}")
    
    try:
        # Make the request
        response = requests.get(api_url)
        
        # Check status code
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            # Success - print the response
            project = response.json()
            logger.info(f"Successfully retrieved project: {project.get('title_and_location', 'Unknown')}")
            
            # Print the full JSON
            print("\nFull project JSON:")
            print(json.dumps(project, indent=2))
            
        else:
            # Error - print the error message
            logger.error(f"Error response: {response.text}")
            
        return 0 if response.status_code == 200 else 1
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python
"""
Test script to directly run the get_all_projects function
"""
import logging
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_script")

# Import database function
from database import get_all_projects

def main():
    """Test the get_all_projects function directly"""
    logger.info("=== Testing get_all_projects function directly ===")
    
    try:
        # Call the function
        projects = get_all_projects()
        
        # Log the results
        logger.info(f"Function returned {len(projects)} projects")
        
        # Print each project
        for i, project in enumerate(projects):
            logger.info(f"Project {i+1}: ID={project.id}, Title={project.title_and_location}, Owner={project.project_owner}")
        
        # Convert to dict for JSON display
        projects_dict = [p.model_dump() for p in projects]
        print("\nProjects as JSON:")
        print(json.dumps(projects_dict, indent=2))
        
        return 0
    except Exception as e:
        logger.error(f"Error testing get_all_projects: {str(e)}")
        logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
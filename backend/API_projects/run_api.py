#!/usr/bin/env python3
import os
import sys
import logging
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_api")

# Add parent directory to path for imports
parent_dir = Path(__file__).resolve().parent
backend_dir = parent_dir.parent
sys.path.append(str(parent_dir))
sys.path.append(str(backend_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    
    # Load from root .env file
    root_env_path = Path(parent_dir).parent.parent / ".env"
    if root_env_path.exists():
        load_dotenv(root_env_path)
        logger.info(f"Loaded environment variables from {root_env_path}")
    else:
        logger.warning(f"Root .env file not found at {root_env_path}")
except ImportError:
    logger.warning("python-dotenv not installed, skipping .env loading")

# Optional: Verify data structure from a sample project
def validate_project_data_structure():
    """Verify a sample project to ensure data structure is correct"""
    try:
        from database import get_all_projects, get_project_by_id
        
        # Get a list of projects
        projects = get_all_projects()
        if not projects:
            logger.warning("No projects found in database to validate")
            return
        
        # Get details of first project
        project_id = projects[0].id
        logger.info(f"Validating data structure using project: {project_id}")
        
        project = get_project_by_id(project_id)
        if not project:
            logger.warning(f"Could not retrieve project {project_id} for validation")
            return
        
        # Check that all fields are present
        required_fields = [
            'id', 'title_and_location', 'year_completed', 'project_owner', 
            'point_of_contact_name', 'point_of_contact', 'brief_description', 
            'firms_from_section_c'
        ]
        
        missing_fields = [field for field in required_fields if not hasattr(project, field)]
        
        if missing_fields:
            logger.error(f"Missing required fields in project data: {missing_fields}")
        else:
            logger.info("✅ Project data structure validation passed")
            
        # Validate year_completed structure
        if hasattr(project, 'year_completed'):
            year_fields = ['professional_services', 'construction']
            missing_year_fields = [field for field in year_fields if not hasattr(project.year_completed, field)]
            
            if missing_year_fields:
                logger.error(f"Missing required fields in year_completed: {missing_year_fields}")
            else:
                logger.info("✅ Year completed structure validation passed")
        
        # Validate firms structure if any firms exist
        if hasattr(project, 'firms_from_section_c') and project.firms_from_section_c:
            firm = project.firms_from_section_c[0]
            firm_fields = ['firm_name', 'firm_location', 'role']
            missing_firm_fields = [field for field in firm_fields if not hasattr(firm, field)]
            
            if missing_firm_fields:
                logger.error(f"Missing required fields in firms_from_section_c: {missing_firm_fields}")
            else:
                logger.info("✅ Firms structure validation passed")
        
        logger.info(f"Sample project data: {project}")
        
    except Exception as e:
        logger.error(f"Error validating project data structure: {str(e)}")

# Main execution
if __name__ == "__main__":
    logger.info("Starting Project Profiles API")
    
    # Validate data structure before starting the server
    validate_project_data_structure()
    
    # Start API server
    from main import app
    
    # Use environment variables for host and port if available
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    
    logger.info(f"API server starting on {host}:{port}")
    uvicorn.run(app, host=host, port=port) 
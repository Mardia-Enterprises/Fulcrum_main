#!/usr/bin/env python3
"""
Script to validate and repair existing projects in the database.
This helps ensure all projects conform to the expected data structure.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("repair_projects")

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

# Import necessary database functions
from database import get_all_projects, get_project_by_id, update_project
from models import ProjectUpdate, YearCompleted, Firm

def validate_and_repair_projects():
    """Validate all projects and repair any with structural issues"""
    logger.info("Starting project validation and repair process")
    
    # Get all projects
    projects = get_all_projects()
    if not projects:
        logger.warning("No projects found in database")
        return
    
    logger.info(f"Found {len(projects)} projects to validate")
    
    repaired_count = 0
    errors_count = 0
    
    # Process each project
    for idx, proj in enumerate(projects):
        logger.info(f"Processing project {idx+1}/{len(projects)}: {proj.id}")
        
        try:
            # Get full project details
            project = get_project_by_id(proj.id)
            if not project:
                logger.warning(f"Could not retrieve project {proj.id}")
                continue
            
            # Check for structural issues
            has_issues = False
            update_data = ProjectUpdate()
            
            # Check year_completed structure
            if not hasattr(project, 'year_completed') or project.year_completed is None:
                has_issues = True
                update_data.year_completed = YearCompleted(
                    professional_services=None,
                    construction=None
                )
                logger.info(f"Project {proj.id} missing year_completed, will repair")
            
            # Check firms structure
            if not hasattr(project, 'firms_from_section_c') or project.firms_from_section_c is None:
                has_issues = True
                update_data.firms_from_section_c = []
                logger.info(f"Project {proj.id} missing firms_from_section_c, will repair")
            elif len(project.firms_from_section_c) > 0:
                # Validate each firm
                fixed_firms = []
                for firm in project.firms_from_section_c:
                    if not all(hasattr(firm, field) for field in ['firm_name', 'firm_location', 'role']):
                        has_issues = True
                        fixed_firms.append(Firm(
                            firm_name=getattr(firm, 'firm_name', "Unknown"),
                            firm_location=getattr(firm, 'firm_location', "Unknown"),
                            role=getattr(firm, 'role', "Unknown")
                        ))
                    else:
                        fixed_firms.append(firm)
                
                if has_issues:
                    update_data.firms_from_section_c = fixed_firms
                    logger.info(f"Project {proj.id} has firms with issues, will repair")
            
            # Check other required fields
            required_fields = [
                'title_and_location', 'project_owner', 'point_of_contact_name', 
                'point_of_contact', 'brief_description'
            ]
            
            for field in required_fields:
                if not hasattr(project, field) or getattr(project, field) is None:
                    has_issues = True
                    setattr(update_data, field, "Unknown" if field != 'brief_description' else "No description available")
                    logger.info(f"Project {proj.id} missing {field}, will repair")
            
            # Apply updates if needed
            if has_issues:
                logger.info(f"Repairing project {proj.id}")
                updated = update_project(proj.id, update_data)
                if updated:
                    logger.info(f"Successfully repaired project {proj.id}")
                    repaired_count += 1
                else:
                    logger.error(f"Failed to repair project {proj.id}")
                    errors_count += 1
            else:
                logger.info(f"Project {proj.id} has valid structure, no repair needed")
            
        except Exception as e:
            logger.error(f"Error processing project {proj.id}: {str(e)}")
            errors_count += 1
    
    logger.info(f"Project validation complete: {repaired_count} repaired, {errors_count} errors")

if __name__ == "__main__":
    validate_and_repair_projects() 
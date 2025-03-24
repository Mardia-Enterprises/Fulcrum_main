import os
import json
import sys
import logging
from typing import List, Dict, Any, Optional

# Configure logging
from utils import setup_logging
logger = setup_logging()

# Load environment variables from root .env file
from dotenv import load_dotenv
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

# Import generate_embedding from utils
from utils import generate_embedding

# Import our supabase adapter
from supabase_adapter import query_index, fetch_vectors, delete_vectors

# Import models
from models import ProjectResponse, ProjectDetail

def format_project_data(title_and_location: str, year_completed: Dict[str, Any] = None,
                      project_owner: str = None, point_of_contact_name: str = None,
                      point_of_contact_telephone_number: str = None, brief_description: str = None,
                      firms_from_section_c_involved_with_this_project: List[Dict[str, Any]] = None,
                      file_id: Any = None) -> Dict[str, Any]:
    """
    Format project data consistently to ensure proper storage and retrieval.
    Provides default values for missing fields.
    """
    # Ensure consistent formatting of project data
    return {
        "title_and_location": title_and_location,
        "year_completed": year_completed or {
            "professional_services": None,
            "construction": None
        },
        "project_owner": project_owner or "Not provided",
        "point_of_contact_name": point_of_contact_name or "Not provided",
        "point_of_contact_telephone_number": point_of_contact_telephone_number or "Not provided",
        "brief_description": brief_description or "Not provided",
        "firms_from_section_c_involved_with_this_project": firms_from_section_c_involved_with_this_project or [],
        "file_id": file_id
    }

def get_all_projects() -> List[ProjectResponse]:
    """
    Retrieve all projects from Supabase by directly querying the database table
    """
    try:
        # Use our supabase adapter to directly access the database
        from supabase_adapter import supabase
        
        logger.info("Directly querying Supabase table for ALL projects")
        
        # Query all rows from the section_f_projects table directly
        result = supabase.table('section_f_projects').select('*').execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching projects from Supabase: {result.error}")
            return []
        
        logger.info(f"Raw database result count: {len(result.data)}")
        
        projects = []
        for item in result.data:
            try:
                # Skip the embedding field to avoid memory issues
                if 'embedding' in item:
                    del item['embedding']
                    
                # Extract and parse project_data
                project_data = item.get('project_data', {})
                
                # Check if project_data is a string that needs parsing
                if isinstance(project_data, str):
                    try:
                        project_data = json.loads(project_data)
                    except Exception as e:
                        logger.error(f"Failed to parse project_data string for project {item.get('id', '')}: {e}")
                        project_data = {}
                
                # Get title_and_location with fallbacks
                title_and_location = None
                
                # Try to get title from various sources
                if isinstance(project_data, dict):
                    if 'title_and_location' in project_data:
                        title_and_location = project_data['title_and_location']
                
                # If no title found yet, try project_key from the item
                if not title_and_location and item.get('project_key'):
                    title_and_location = item.get('project_key')
                
                # Last resort - use ID if available
                if not title_and_location and item.get('id'):
                    title_and_location = item.get('id').replace('_', ' ').title()
                    
                # If still no title, use a default
                if not title_and_location:
                    title_and_location = 'Unknown Project'
                
                # Extract project_owner with fallbacks
                project_owner = "Not provided"
                if isinstance(project_data, dict):
                    # First try standard field
                    if 'project_owner' in project_data:
                        project_owner = project_data.get('project_owner')
                    # If project data has budget with fee info, it might have project owner info embedded
                    elif 'budget' in project_data and isinstance(project_data['budget'], dict):
                        budget = project_data['budget']
                        if 'owner' in budget:
                            project_owner = budget['owner']
                
                # Extract brief_description with fallbacks
                brief_description = "Not provided"
                if isinstance(project_data, dict):
                    if 'brief_description' in project_data:
                        brief_description = project_data.get('brief_description')
                    # Try alternate keys
                    elif 'description' in project_data:
                        brief_description = project_data.get('description')
                    elif 'scope' in project_data:
                        brief_description = project_data.get('scope')
                
                # Get year_completed with fallbacks
                year_completed = None
                if isinstance(project_data, dict):
                    if 'year_completed' in project_data:
                        year_completed = project_data.get('year_completed')
                    # If there are budget keys with dates, try to extract year info
                    elif 'budget' in project_data and isinstance(project_data['budget'], dict):
                        budget = project_data['budget']
                        if 'year' in budget:
                            year_completed = {"construction": budget['year']}
                
                # Handle budget data if present 
                budget_info = {}
                if isinstance(project_data, dict) and 'budget' in project_data:
                    budget = project_data['budget']
                    if isinstance(budget, dict):
                        if 'fee' in budget:
                            budget_info['fee'] = budget['fee']
                        if 'cost' in budget:
                            budget_info['cost'] = budget['cost']
                            
                # Try directly extracting budget data from the top level
                elif isinstance(project_data, dict):
                    # Handle the {"budget":{"fee":"$2.9M","cost":"$65M"}}
                    if isinstance(project_data, dict) and isinstance(project_data.get('budget'), dict):
                        budget = project_data['budget']
                        if 'fee' in budget:
                            budget_info['fee'] = budget['fee']
                        if 'cost' in budget:
                            budget_info['cost'] = budget['cost']
                    # Handle the bare {"fee":"$4M","cost":"$40M"} format
                    elif 'fee' in project_data:
                        budget_info['fee'] = project_data['fee']
                        if 'cost' in project_data:
                            budget_info['cost'] = project_data['cost']
                
                # Log each project being processed
                logger.info(f"Processing project: {title_and_location} with ID: {item.get('id', '')}")
                
                # Create a ProjectResponse object - these fields are required by the model
                project_response = {
                    "title_and_location": title_and_location,
                    "project_owner": project_owner,
                    "score": 1.0,  # Default high score for listed projects
                }
                
                # Add optional fields if they exist
                if year_completed:
                    project_response["year_completed"] = year_completed
                if brief_description:
                    project_response["brief_description"] = brief_description
                if budget_info:
                    project_response["budget_info"] = budget_info
                
                # Add to the projects list - use ** to expand the dict into kwargs
                projects.append(ProjectResponse(**project_response))
                
            except Exception as project_error:
                logger.error(f"Error processing project {item.get('id', '')}: {str(project_error)}")
                # Try to add a minimal project with just the ID to ensure all projects get returned
                try:
                    fallback_id = item.get('id', f"unknown_{len(projects)}")
                    fallback_title = item.get('project_key', fallback_id.replace('_', ' ').title())
                    projects.append(ProjectResponse(
                        title_and_location=fallback_title,
                        project_owner="Error retrieving data",
                        score=0.1,
                        brief_description=f"Error processing project data: {str(project_error)[:100]}..."
                    ))
                except:
                    # Last resort - just log and continue
                    logger.error(f"Failed to create even a fallback project for {item.get('id', 'unknown')}")
                    continue
        
        logger.info(f"Final project list count: {len(projects)}")
        return projects
    
    except Exception as e:
        logger.error(f"Error in get_all_projects: {str(e)}")
        return []

def get_project_by_title(project_title: str) -> Optional[ProjectDetail]:
    """
    Retrieve a specific project by title
    
    Args:
        project_title: The title of the project to retrieve
        
    Returns:
        ProjectDetail object if found, None otherwise
    """
    try:
        # Use our supabase adapter to directly access the database
        from supabase_adapter import supabase
        
        logger.info(f"Looking up project by title: {project_title}")
        
        # Convert project title to a valid id format (matching storage format)
        project_id = project_title.lower().replace(' ', '_').replace(',', '')
        
        # Try to fetch by ID first (most reliable)
        result = supabase.table('section_f_projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching project by ID: {result.error}")
            return None
        
        # If we didn't find by ID, try with ILIKE on project_key
        if not result.data:
            logger.info(f"Project not found by ID, trying with ILIKE on project_key: {project_title}")
            result = supabase.table('section_f_projects').select('*').ilike('project_key', f'%{project_title}%').execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error fetching project by title: {result.error}")
                return None
        
        # If still no results, return None
        if not result.data:
            logger.warning(f"No project found with title similar to: {project_title}")
            return None
        
        # Get the first result
        item = result.data[0]
        
        # Extract and parse project_data
        project_data = item.get('project_data', {})
        
        # Check if project_data is a string that needs parsing
        if isinstance(project_data, str):
            try:
                project_data = json.loads(project_data)
            except Exception as e:
                logger.error(f"Failed to parse project_data string: {e}")
        
        # Create ProjectDetail object from the data
        return ProjectDetail(
            title_and_location=project_data.get('title_and_location', item.get('project_key', 'Unknown Project')),
            year_completed=project_data.get('year_completed', {}),
            project_owner=project_data.get('project_owner', 'Not provided'),
            point_of_contact_name=project_data.get('point_of_contact_name', 'Not provided'),
            point_of_contact_telephone_number=project_data.get('point_of_contact_telephone_number', 'Not provided'),
            brief_description=project_data.get('brief_description', 'Not provided'),
            firms_from_section_c_involved_with_this_project=project_data.get('firms_from_section_c_involved_with_this_project', []),
            file_id=project_data.get('file_id', item.get('file_id', None))
        )
    
    except Exception as e:
        logger.error(f"Error in get_project_by_title: {str(e)}")
        return None

def delete_project_by_title(project_title: str) -> bool:
    """
    Delete a project by title
    
    Args:
        project_title: The title of the project to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use our supabase adapter to directly access the database
        from supabase_adapter import supabase
        
        logger.info(f"Deleting project by title: {project_title}")
        
        # Convert project title to a valid id format (matching storage format)
        project_id = project_title.lower().replace(' ', '_').replace(',', '')
        
        # First, check if the project exists
        result = supabase.table('section_f_projects').select('id').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error checking project existence: {result.error}")
            return False
        
        if not result.data:
            logger.warning(f"No project found with title: {project_title}")
            return False
        
        # Delete from Supabase table
        delete_result = supabase.table('section_f_projects').delete().eq('id', project_id).execute()
        
        if hasattr(delete_result, 'error') and delete_result.error:
            logger.error(f"Error deleting project: {delete_result.error}")
            return False
        
        logger.info(f"Successfully deleted project: {project_title}")
        return True
    
    except Exception as e:
        logger.error(f"Error in delete_project_by_title: {str(e)}")
        return False 
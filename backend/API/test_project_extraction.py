import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

# Add resume_parser_f directory to path for project creation
resume_parser_f_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resume_parser_f"))
sys.path.append(resume_parser_f_dir)
# Ensure parent directory is also in path to avoid import issues
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Try to import the required function
try:
    from resume_parser_f.dataparser import upsert_project_in_supabase
    logger.info(f"Successfully imported upsert_project_in_supabase from resume_parser_f")
except ImportError as e:
    logger.error(f"Error importing from resume_parser_f: {str(e)}")
    logger.error(f"Current sys.path: {sys.path}")
    
    # Fallback implementation
    def upsert_project_in_supabase(project_title, file_id, project_data):
        logger.error("Using fallback implementation of upsert_project_in_supabase")
        logger.error("This is just for testing - no data will be stored in Supabase")
        logger.info(f"Would have stored project: {project_title}")
        logger.info(f"Project data: {json.dumps(project_data, indent=2)}")
        return project_title.lower().replace(' ', '_').replace(',', '')

# Import database functions
from database import get_employee_by_name

def extract_and_create_projects(employee_name):
    """
    Extract projects from an employee's relevant_projects field and create them
    in the projects database (section_f_projects table).
    
    Args:
        employee_name: The name of the employee whose projects to extract
        
    Returns:
        List of created projects
    """
    logger.info(f"Extracting projects from employee: {employee_name}")
    
    # Get the employee data
    employee_data = get_employee_by_name(employee_name)
    if not employee_data:
        logger.error(f"Employee '{employee_name}' not found")
        return []
    
    # Convert Pydantic model to dict if needed
    if hasattr(employee_data, "dict"):
        # It's a Pydantic model
        employee_dict = employee_data.dict()
    elif hasattr(employee_data, "get"):
        # It's already a dict
        employee_dict = employee_data
    else:
        # Try to extract attributes directly
        employee_dict = {}
        for attr in ["relevant_projects", "firm", "role"]:
            if hasattr(employee_data, attr):
                employee_dict[attr] = getattr(employee_data, attr)
    
    # Extract relevant projects
    relevant_projects = employee_dict.get("relevant_projects", [])
    if not relevant_projects:
        logger.info("No projects found for this employee")
        return []
    
    # Track created projects
    created_projects = []
    
    # Process each project
    for project in relevant_projects:
        # Skip if project is not a dict or doesn't have required fields
        if not isinstance(project, dict):
            logger.warning(f"Invalid project format: {project}")
            continue
            
        # Extract title and location from project
        title_and_location = None
        if "title_and_location" in project and project["title_and_location"]:
            title_and_location = project["title_and_location"]
        elif isinstance(project.get("title_and_location"), list) and len(project["title_and_location"]) >= 2:
            # Handle case where title_and_location is a list with [title, location]
            title_and_location = ", ".join(project["title_and_location"])
        
        if not title_and_location:
            logger.warning(f"Missing title for project: {project}")
            continue
        
        # Create a project object structured for section_f_projects
        project_data = {
            "title_and_location": title_and_location,
            "year_completed": {
                "professional_services": None,
                "construction": None
            },
            "project_owner": project.get("project_owner", "Not provided"),
            "point_of_contact_name": "Not provided",
            "point_of_contact_telephone_number": "Not provided",
            "brief_description": project.get("scope", "Not provided"),
            "firms_from_section_c_involved_with_this_project": []
        }
        
        # Add fee and cost if available
        if "fee" in project or "cost" in project:
            project_data["budget"] = {
                "fee": project.get("fee", "Not provided"),
                "cost": project.get("cost", "Not provided")
            }
        
        # Function to safely get firm information
        def get_firm_info(key, default="Not provided"):
            if hasattr(employee_dict.get("firm", {}), "get"):
                return employee_dict.get("firm", {}).get(key, default)
            elif hasattr(employee_dict.get("firm", {}), key):
                return getattr(employee_dict.get("firm", {}), key)
            return default
        
        # Add role information
        if "role" in project:
            if isinstance(project["role"], list):
                # If role is a list, create a firm entry for each role
                for role in project["role"]:
                    project_data["firms_from_section_c_involved_with_this_project"].append({
                        "firm_name": get_firm_info("Name"),
                        "firm_location": get_firm_info("Location"),
                        "role": role
                    })
            else:
                # Single role
                project_data["firms_from_section_c_involved_with_this_project"].append({
                    "firm_name": get_firm_info("Name"),
                    "firm_location": get_firm_info("Location"),
                    "role": project["role"]
                })
        
        # Generate a unique file_id for the project
        file_id = f"from_employee_{employee_name.replace(' ', '_').lower()}"
        
        # Get employee role safely
        employee_role = employee_dict.get("role", "Not provided")
        if not isinstance(employee_role, str) and hasattr(employee_role, "__str__"):
            employee_role = str(employee_role)
        
        # Add the employee as a key person
        project_data["key_personnel"] = [{
            "name": employee_name,
            "role": employee_role
        }]
        
        # Print project data for review
        logger.info(f"Project data for {title_and_location}:")
        logger.info(json.dumps(project_data, indent=2))
        
        # Ensure title_and_location is a string
        if isinstance(title_and_location, list):
            title_and_location = ", ".join(title_and_location)
        
        # Store the project in Supabase
        project_id = upsert_project_in_supabase(title_and_location, file_id, project_data)
        
        # Add to list of created projects
        created_projects.append({
            "project_id": project_id,
            "title": title_and_location
        })
    
    return created_projects

if __name__ == "__main__":
    # Check if employee name is provided via command line
    if len(sys.argv) > 1:
        employee_name = sys.argv[1]
    else:
        # Demo with a specific employee if none provided
        employee_name = "Michael Chopin"  # Replace with a name known to exist in your database
    
    # Extract and create projects
    created_projects = extract_and_create_projects(employee_name)
    
    # Print results
    print(f"\nCreated {len(created_projects)} projects for {employee_name}:")
    for project in created_projects:
        print(f"- {project['title']} (ID: {project['project_id']})") 
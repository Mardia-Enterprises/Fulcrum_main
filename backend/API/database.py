import os
import json
import sys
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("database")

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
from models import EmployeeResponse, EmployeeDetail

def get_all_employees() -> List[EmployeeResponse]:
    """
    Retrieve all employees from Supabase
    """
    try:
        # Use our supabase adapter to query all employees
        from supabase_adapter import query_index
        
        # Directly query all employees
        results = query_index(
            query_text="all employees",
            top_k=100,  # Adjust based on expected number of employees
            match_threshold=0.01  # Use a very low threshold
        )
        
        employees = []
        for employee in results:
            # Process role which could be a list
            role_list = employee.get("role", [])
            role_str = ", ".join(role_list) if isinstance(role_list, list) else str(role_list)
            
            # Extract education which could be a list
            education_list = employee.get("education", [])
            education_str = ", ".join(education_list) if isinstance(education_list, list) else str(education_list)
            if not education_str or education_str == "[]":
                education_str = "Not provided"
            
            # Get the complete data from Supabase for this employee
            from supabase_adapter import fetch_vectors
            employee_id = employee.get("id", "")
            
            # Add employee with available data
            employees.append(
                EmployeeResponse(
                    name=employee.get("name", "Unknown"),
                    role=role_str,
                    score=employee.get("score", 0),
                    education=education_str,
                    years_experience=employee.get("years_experience", "Not provided"),
                    relevant_projects=employee.get("relevant_projects", [])
                )
            )
        
        return employees
    
    except Exception as e:
        logger.error(f"Error retrieving all employees: {str(e)}")
        return []

def get_employee_by_name(employee_name: str) -> Optional[EmployeeDetail]:
    """
    Retrieve a specific employee by name
    """
    try:
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee_name.lower().replace(' ', '_')
        
        # Fetch the vector by ID (employee name)
        fetch_response = fetch_vectors(ids=[employee_id])
        
        if not fetch_response.vectors or employee_id not in fetch_response.vectors:
            logger.warning(f"Employee not found: {employee_name}")
            return None
        
        vector = fetch_response.vectors[employee_id]
        employee_data = json.loads(vector.metadata["resume_data"])
        
        return EmployeeDetail(
            name=employee_data.get("Name", "Unknown"),
            role=employee_data.get("Role in Contract"),
            years_experience=employee_data.get("Years of Experience"),
            firm=employee_data.get("Firm Name & Location"),
            education=employee_data.get("Education"),
            professional_registrations=employee_data.get("Professional Registrations"),
            other_qualifications=employee_data.get("Other Professional Qualifications"),
            relevant_projects=employee_data.get("Relevant Projects"),
            file_id=employee_data.get("file_id")
        )
    
    except Exception as e:
        logger.error(f"Error fetching employee {employee_name}: {str(e)}")
        return None

def get_employees_by_role(role: str) -> List[EmployeeResponse]:
    """
    Retrieve employees by role
    """
    try:
        # Use our supabase adapter to query employees by role
        from supabase_adapter import query_index
        
        # Query for employees with the specified role
        results = query_index(
            query_text=f"employees with role {role}",
            top_k=100,  # Adjust based on expected number of employees
            match_threshold=0.01  # Use a very low threshold
        )
        
        employees = []
        for employee in results:
            # Get role as string for display
            role_list = employee.get("role", [])
            role_str = ", ".join(role_list) if isinstance(role_list, list) else str(role_list)
            
            # Extract education which could be a list
            education_list = employee.get("education", [])
            education_str = ", ".join(education_list) if isinstance(education_list, list) else str(education_list)
            if not education_str or education_str == "[]":
                education_str = "Not provided"
            
            # Only include employees with matching role (case-insensitive)
            if isinstance(role_list, list) and any(role.lower() in r.lower() for r in role_list):
                employees.append(
                    EmployeeResponse(
                        name=employee.get("name", "Unknown"),
                        role=role_str,
                        score=employee.get("score", 0),
                        education=education_str,
                        years_experience=employee.get("years_experience", "Not provided"),
                        relevant_projects=employee.get("relevant_projects", [])
                    )
                )
        
        return employees
    
    except Exception as e:
        logger.error(f"Error retrieving employees by role {role}: {str(e)}")
        return []

def delete_employee_by_name(employee_name: str) -> bool:
    """
    Delete an employee by name
    """
    try:
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee_name.lower().replace(' ', '_')
        
        # Check if employee exists
        fetch_response = fetch_vectors(ids=[employee_id])
        if not fetch_response.vectors or employee_id not in fetch_response.vectors:
            logger.warning(f"Employee not found for deletion: {employee_name}")
            return False
        
        # Delete the vector
        success = delete_vectors(ids=[employee_id])
        if success:
            logger.info(f"Successfully deleted employee: {employee_name}")
        else:
            logger.error(f"Failed to delete employee: {employee_name}")
        
        return success
    
    except Exception as e:
        logger.error(f"Error deleting employee {employee_name}: {str(e)}")
        return False 
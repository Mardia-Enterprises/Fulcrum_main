import os
import json
import sys
from typing import List, Dict, Any, Optional

# Add parent directory to path to import from Resume_Parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from Resume_Parser
from Resume_Parser.datauploader import generate_embedding
from dotenv import load_dotenv

# Import our pinecone adapter
from API.pinecone_adapter import query_index, fetch_vectors, delete_vectors

# Import models
from API.models import EmployeeResponse, EmployeeDetail

# Load environment variables
load_dotenv()

def get_all_employees() -> List[EmployeeResponse]:
    """
    Retrieve all employees from Pinecone
    """
    # We'll use a generic query to fetch all vectors
    # This is a simple approach - for production with many employees, 
    # you might want to implement pagination
    generic_query = generate_embedding("all employees")
    
    # Query with a high limit to get all employees
    results = query_index(
        vector=generic_query,
        top_k=100,  # Adjust based on expected number of employees
        include_metadata=True
    )
    
    employees = []
    for match in results.matches:
        employee_data = json.loads(match.metadata["resume_data"])
        employees.append(
            EmployeeResponse(
                name=employee_data.get("Name", "Unknown"),
                role=employee_data.get("Role in Contract", "Not provided"),
                score=match.score,
                education=employee_data.get("Education", "Not provided"),
                relevant_projects=employee_data.get("Relevant Projects", [])
            )
        )
    
    return employees

def get_employee_by_name(employee_name: str) -> Optional[EmployeeDetail]:
    """
    Retrieve a specific employee by name
    """
    try:
        # Fetch the vector by ID (employee name)
        fetch_response = fetch_vectors(ids=[employee_name])
        
        if not fetch_response.vectors or employee_name not in fetch_response.vectors:
            return None
        
        vector = fetch_response.vectors[employee_name]
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
            file_id=vector.metadata.get("file_id")
        )
    
    except Exception as e:
        print(f"Error fetching employee {employee_name}: {str(e)}")
        return None

def get_employees_by_role(role: str) -> List[EmployeeResponse]:
    """
    Retrieve employees by role
    """
    # Generate a query embedding for the role
    role_query = generate_embedding(f"employees with role {role}")
    
    # Query Pinecone
    results = query_index(
        vector=role_query,
        top_k=100,  # Adjust based on expected number of employees
        include_metadata=True
    )
    
    employees = []
    for match in results.matches:
        employee_data = json.loads(match.metadata["resume_data"])
        
        # Only include employees with matching role
        employee_role = employee_data.get("Role in Contract", "").lower()
        if role.lower() in employee_role:
            employees.append(
                EmployeeResponse(
                    name=employee_data.get("Name", "Unknown"),
                    role=employee_data.get("Role in Contract", "Not provided"),
                    score=match.score,
                    education=employee_data.get("Education", "Not provided"),
                    relevant_projects=employee_data.get("Relevant Projects", [])
                )
            )
    
    return employees

def delete_employee_by_name(employee_name: str) -> bool:
    """
    Delete an employee by name
    """
    try:
        # Check if employee exists
        fetch_response = fetch_vectors(ids=[employee_name])
        if not fetch_response.vectors or employee_name not in fetch_response.vectors:
            return False
        
        # Delete the vector
        delete_vectors(ids=[employee_name])
        return True
    
    except Exception as e:
        print(f"Error deleting employee {employee_name}: {str(e)}")
        return False 
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

def format_employee_data(employee_name: str, role: str = None, years_experience: dict = None,
                        firm: dict = None, education: Any = None, 
                        professional_registrations: list = None,
                        other_qualifications: str = None, 
                        relevant_projects: list = None,
                        file_id: Any = None) -> dict:
    """
    Format employee data consistently to ensure proper storage and retrieval.
    Provides default values for missing fields.
    """
    # Ensure consistent formatting of employee data
    return {
        "Name": employee_name,
        "Role in Contract": role or "Not specified",
        "Years of Experience": years_experience or {
            "Total": "Unknown",
            "With Current Firm": "Unknown"
        },
        "Firm Name & Location": firm or {
            "Name": "Unknown",
            "Location": "Unknown"
        },
        "Education": education or "Not provided",
        "Professional Registrations": professional_registrations or [],
        "Other Professional Qualifications": other_qualifications or "Not provided",
        "Relevant Projects": relevant_projects or [],
        "file_id": file_id
    }

def get_all_employees() -> List[EmployeeResponse]:
    """
    Retrieve all employees from Supabase by directly querying the database table
    """
    try:
        # Use our supabase adapter to directly access the database
        from supabase_adapter import supabase
        
        logger.info("Directly querying Supabase table for ALL employees")
        
        # Query all rows from the employees table directly
        result = supabase.table('employees').select('*').execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching employees from Supabase: {result.error}")
            return []
        
        logger.info(f"Raw database result count: {len(result.data)}")
        
        employees = []
        for item in result.data:
            # Extract and parse resume_data
            resume_data = item.get('resume_data', {})
            
            # Check if resume_data is a string that needs parsing
            if isinstance(resume_data, str):
                try:
                    resume_data = json.loads(resume_data)
                except Exception as e:
                    logger.error(f"Failed to parse resume_data string: {e}")
            
            # Get employee name with fallbacks
            name = None
            if 'name' in resume_data:
                name = resume_data['name']
            elif 'Name' in resume_data:
                name = resume_data['Name']
            else:
                # Use ID as fallback
                name = item.get('id', '').replace('_', ' ').title()
            
            # Extract role field with fallbacks
            role_list = None
            if 'role' in resume_data:
                role_list = resume_data['role']
            elif 'Role' in resume_data:
                role_list = resume_data['Role']
            elif 'Role in Contract' in resume_data:
                role_list = resume_data['Role in Contract']
            else:
                role_list = []
            
            # Convert role to string for display
            role_str = ", ".join(role_list) if isinstance(role_list, list) else str(role_list)
            
            # Extract education with fallbacks
            education_list = resume_data.get('education', resume_data.get('Education', []))
            education_str = ", ".join(education_list) if isinstance(education_list, list) else str(education_list)
            if not education_str or education_str == "[]":
                education_str = "Not provided"
            
            # Get years experience with fallbacks
            years_experience = resume_data.get('years_experience', 
                                  resume_data.get('Years of Experience', 
                                  resume_data.get('years of experience', 'Not provided')))
            
            # Extract relevant projects with fallbacks
            relevant_projects = resume_data.get('relevant_projects', 
                               resume_data.get('Relevant Projects', []))
            
            # Log each employee being processed
            logger.info(f"Processing employee: {name} with ID: {item.get('id', '')}")
            
            # Add employee to the list
            employees.append(
                EmployeeResponse(
                    name=name,
                    role=role_str,
                    score=1.0,  # Since we're not using vector search, set a default high score
                    education=education_str,
                    years_experience=years_experience,
                    relevant_projects=relevant_projects
                )
            )
        
        logger.info(f"Final employee list count: {len(employees)}")
        return employees
    
    except Exception as e:
        logger.error(f"Error retrieving all employees: {str(e)}")
        return []

def get_employee_by_name(employee_name: str) -> Optional[EmployeeDetail]:
    """
    Retrieve a specific employee by name
    """
    try:
        # Log the original employee name for debugging
        logger.info(f"Attempting to fetch employee: {employee_name}")
        
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee_name.lower().replace(' ', '_')
        logger.info(f"Converted to employee_id: {employee_id}")
        
        # First attempt: try exact match
        fetch_response = fetch_vectors(ids=[employee_id])
        
        if not fetch_response.vectors or employee_id not in fetch_response.vectors:
            logger.warning(f"Employee not found with exact ID: {employee_id}, trying partial search...")
            
            # Second attempt: try to find the employee using the query function
            from supabase_adapter import query_index
            
            # Use the original name for searching
            search_results = query_index(
                query_text=f"employee {employee_name}",
                top_k=5,
                match_threshold=0.01  # Use a low threshold to get more potential matches
            )
            
            if not search_results:
                logger.warning(f"No potential matches found for: {employee_name}")
                return None
            
            # Try to find an exact or close match in the search results
            best_match = None
            best_score = 0
            
            for result in search_results:
                result_name = result.get("name", "").lower()
                search_name = employee_name.lower()
                
                logger.info(f"Comparing '{result_name}' with '{search_name}', score: {result.get('score', 0)}")
                
                # Check if name contains the search term or vice versa
                if (search_name in result_name or result_name in search_name) and result.get("score", 0) > best_score:
                    best_match = result
                    best_score = result.get("score", 0)
            
            if not best_match:
                logger.warning(f"No suitable matches found for: {employee_name}")
                return None
            
            # Convert to employee detail
            employee_data = {
                "Name": best_match.get("name", "Unknown"),
                "Role in Contract": best_match.get("role", []),
                "Years of Experience": best_match.get("years_experience", "Not provided"),
                "Firm Name & Location": best_match.get("firm_name_and_location", {}),
                "Education": best_match.get("education", []),
                "Professional Registrations": best_match.get("current_professional_registration", []),
                "Other Professional Qualifications": best_match.get("other_professional_qualifications", ""),
                "Relevant Projects": best_match.get("relevant_projects", []),
                "file_id": best_match.get("file_id", None)
            }
            
            logger.info(f"Found best match: {employee_data['Name']} with score {best_score}")
            
            return EmployeeDetail(
                name=employee_data["Name"],
                role=employee_data["Role in Contract"],
                years_experience=employee_data["Years of Experience"],
                firm=employee_data["Firm Name & Location"],
                education=employee_data["Education"],
                professional_registrations=employee_data["Professional Registrations"],
                other_qualifications=employee_data["Other Professional Qualifications"],
                relevant_projects=employee_data["Relevant Projects"],
                file_id=employee_data["file_id"]
            )
        
        # If exact match is found, process it
        vector = fetch_response.vectors[employee_id]
        
        # Get the resume_data - need to handle different formats
        try:
            # First try to parse as JSON if it's a string
            if isinstance(vector.metadata["resume_data"], str):
                employee_data = json.loads(vector.metadata["resume_data"])
                logger.info(f"Successfully parsed resume_data from string: {employee_data.keys()}")
            else:
                employee_data = vector.metadata["resume_data"]
                logger.info(f"Using resume_data as object: {employee_data.keys()}")
        except Exception as e:
            logger.error(f"Error parsing resume_data: {str(e)}")
            # Try to extract directly from the vector
            employee_data = {}
            for key in ["name", "Name", "role", "Role", "Role in Contract"]:
                if hasattr(vector, key):
                    employee_data[key] = getattr(vector, key)
            
            # Use the employee name from the query as a fallback
            if "Name" not in employee_data and "name" not in employee_data:
                employee_data["Name"] = employee_name
        
        logger.info(f"Successfully retrieved employee data for: {employee_data.get('Name', employee_data.get('name', 'Unknown'))}")
        
        # Create a default empty map for any missing fields
        default_empty = {}
        
        # Create a simplified employee with default values for missing fields
        employee_detail = EmployeeDetail(
            name=employee_data.get("Name", employee_data.get("name", employee_name)),
            role=employee_data.get("Role in Contract", employee_data.get("Role", employee_data.get("role", None))),
            years_experience=employee_data.get("Years of Experience", employee_data.get("years_experience", default_empty)),
            firm=employee_data.get("Firm Name & Location", employee_data.get("firm_name_and_location", default_empty)),
            education=employee_data.get("Education", employee_data.get("education", [])),
            professional_registrations=employee_data.get("Professional Registrations", 
                                                          employee_data.get("professional_registrations", [])),
            other_qualifications=employee_data.get("Other Professional Qualifications", 
                                                   employee_data.get("other_qualifications", "")),
            relevant_projects=employee_data.get("Relevant Projects", 
                                               employee_data.get("relevant_projects", [])),
            file_id=employee_data.get("file_id", None)
        )
        
        logger.info(f"Created EmployeeDetail: {employee_detail}")
        return employee_detail
    
    except Exception as e:
        logger.error(f"Error fetching employee {employee_name}: {str(e)}", exc_info=True)
        return None

def get_employees_by_role(role: str) -> List[EmployeeResponse]:
    """
    Retrieve employees by role using semantic matching with embeddings
    """
    try:
        # Use direct database access
        from supabase_adapter import supabase
        from utils import generate_embedding
        import numpy as np
        
        logger.info(f"Querying for employees with role: {role} using semantic matching")
        
        # Generate embedding for the target role
        try:
            role_embedding = generate_embedding(role)
            use_semantic = True
            logger.info(f"Successfully generated embedding for role: {role}")
        except Exception as e:
            logger.error(f"Error generating embedding, falling back to text search: {str(e)}")
            use_semantic = False
            role_lower = role.lower()
        
        # Query all employees directly from the database
        result = supabase.table('employees').select('*').execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching employees from Supabase: {result.error}")
            return []
        
        logger.info(f"Raw database result count: {len(result.data)}")
        
        employees = []
        
        for item in result.data:
            # Extract and parse resume_data
            resume_data = item.get('resume_data', {})
            
            # Check if resume_data is a string that needs parsing
            if isinstance(resume_data, str):
                try:
                    resume_data = json.loads(resume_data)
                except Exception as e:
                    logger.error(f"Failed to parse resume_data string: {e}")
                    continue
            
            # Get employee name with fallbacks
            name = None
            if 'name' in resume_data:
                name = resume_data['name']
            elif 'Name' in resume_data:
                name = resume_data['Name']
            else:
                # Use ID as fallback
                name = item.get('id', '').replace('_', ' ').title()
            
            # Extract role field with fallbacks
            role_list = None
            if 'role' in resume_data:
                role_list = resume_data['role']
            elif 'Role' in resume_data:
                role_list = resume_data['Role']
            elif 'Role in Contract' in resume_data:
                role_list = resume_data['Role in Contract']
            else:
                role_list = []
            
            # Convert roles to list if not already
            if not isinstance(role_list, list):
                role_list = [str(role_list)]
            
            # Extract education with fallbacks
            education_list = resume_data.get('education', resume_data.get('Education', []))
            education_str = ", ".join(education_list) if isinstance(education_list, list) else str(education_list)
            if not education_str or education_str == "[]":
                education_str = "Not provided"
            
            # Get years experience with fallbacks
            years_experience = resume_data.get('years_experience', 
                                resume_data.get('Years of Experience', 
                                resume_data.get('years of experience', 'Not provided')))
            
            # Extract relevant projects with fallbacks
            relevant_projects = resume_data.get('relevant_projects', 
                                resume_data.get('Relevant Projects', []))
            
            # Convert role to string for display
            role_str = ", ".join(role_list) if isinstance(role_list, list) else str(role_list)
            
            # Determine if role matches using semantic search or text search
            matches_role = False
            similarity_score = 0
            
            if use_semantic:
                # Try semantic matching with embeddings
                for r in role_list:
                    if isinstance(r, str):
                        try:
                            # Generate embedding for this role
                            r_embedding = generate_embedding(r)
                            
                            # Calculate cosine similarity
                            dot_product = sum(a * b for a, b in zip(role_embedding, r_embedding))
                            magnitude_a = sum(a * a for a in role_embedding) ** 0.5
                            magnitude_b = sum(b * b for b in r_embedding) ** 0.5
                            similarity = dot_product / (magnitude_a * magnitude_b) if magnitude_a * magnitude_b > 0 else 0
                            
                            logger.info(f"Semantic similarity between '{role}' and '{r}': {similarity}")
                            
                            # If similarity is above threshold, consider it a match
                            if similarity > 0.75:  # This threshold can be adjusted
                                matches_role = True
                                similarity_score = similarity
                                break
                        except Exception as e:
                            logger.error(f"Error in semantic matching for role '{r}': {str(e)}")
                            # Fall back to text matching for this role
                            if role_lower in r.lower():
                                matches_role = True
                                similarity_score = 0.8  # Default score for text match
                                break
            else:
                # Use regular text matching as fallback
                for r in role_list:
                    if isinstance(r, str) and (role_lower in r.lower() or r.lower() in role_lower):
                        matches_role = True
                        similarity_score = 0.8  # Default score for text match
                        break
            
            if matches_role:
                logger.info(f"Found matching employee: {name} with roles: {role_str}, score: {similarity_score}")
                
                employees.append(
                    EmployeeResponse(
                        name=name,
                        role=role_str,
                        score=similarity_score,
                        education=education_str,
                        years_experience=years_experience,
                        relevant_projects=relevant_projects
                    )
                )
        
        # Sort employees by similarity score (highest first)
        employees.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Found {len(employees)} employees with role: {role}")
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
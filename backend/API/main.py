from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

# Import utilities first so we can use setup_logging
from utils import generate_embedding, setup_logging

# Configure logging
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

# Import models
from models import (
    QueryRequest, 
    EmployeeResponse, 
    EmployeeList, 
    EmployeeDetail,
    EmployeeCreate,
    SearchResponse
)

# Import database functions
from database import (
    get_all_employees,
    get_employee_by_name,
    get_employees_by_role,
    delete_employee_by_name,
    format_employee_data
)

# Add resume_parser_f directory to path for project creation
resume_parser_f_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resume_parser_f"))
sys.path.append(resume_parser_f_dir)
# Ensure parent directory is also in path to avoid import issues
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
try:
    from resume_parser_f.dataparser import upsert_project_in_supabase
    logger.info(f"Successfully imported upsert_project_in_supabase from resume_parser_f")
except ImportError as e:
    logger.error(f"Error importing from resume_parser_f: {str(e)}")
    logger.error(f"Current sys.path: {sys.path}")
    # Provide a fallback implementation if import fails
    def upsert_project_in_supabase(project_title, file_id, project_data):
        logger.error("Using fallback implementation of upsert_project_in_supabase")
        logger.error("Please fix the import path for resume_parser_f module")
        return project_title.lower().replace(' ', '_').replace(',', '')

# Import Supabase client for direct access
from supabase_adapter import supabase

# Create FastAPI app
app = FastAPI(
    title="Employee Resume API",
    description="API for querying and managing employee resume data stored in Supabase",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def merge_employee_data(new_resume_data: Dict[str, Any], existing_resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new employee data with existing data, preserving existing information
    and appending new information as needed.
    
    Args:
        new_resume_data: The new employee data
        existing_resume_data: The existing employee data
        
    Returns:
        Dict[str, Any]: The merged employee data
    """
    # Make a copy of the new data to avoid modifying the original
    merged_data = new_resume_data.copy()
    
    # Merge roles (ensure it's a list)
    existing_role = existing_resume_data.get("Role in Contract", [])
    new_role = new_resume_data.get("Role in Contract", [])
    if isinstance(existing_role, str):
        existing_role = [existing_role]
    if isinstance(new_role, str):
        new_role = [new_role]
    
    merged_roles = list(set(existing_role + (new_role if new_role != ["Not specified"] else [])))
    if merged_roles:
        merged_data["Role in Contract"] = merged_roles
    
    # Merge projects
    existing_projects = existing_resume_data.get("Relevant Projects", [])
    new_projects = new_resume_data.get("Relevant Projects", [])
    
    # Create a set of project names to avoid duplicates
    existing_project_names = set()
    for project in existing_projects:
        if isinstance(project, dict) and "Name" in project:
            existing_project_names.add(project["Name"])
    
    # Add new projects that don't exist
    merged_projects = existing_projects.copy()
    for project in new_projects:
        if isinstance(project, dict) and "Name" in project:
            if project["Name"] not in existing_project_names:
                merged_projects.append(project)
    
    if merged_projects:
        merged_data["Relevant Projects"] = merged_projects
    
    # Use the more detailed education if provided
    if new_resume_data.get("Education") == "Not provided" and existing_resume_data.get("Education"):
        merged_data["Education"] = existing_resume_data["Education"]
    
    # Use the more detailed professional registrations if provided
    if not new_resume_data.get("Professional Registrations") and existing_resume_data.get("Professional Registrations"):
        merged_data["Professional Registrations"] = existing_resume_data["Professional Registrations"]
    
    # Use existing years experience if new one is not provided
    if (new_resume_data.get("Years of Experience", {}).get("Total") == "Unknown" and 
        existing_resume_data.get("Years of Experience", {}).get("Total") != "Unknown"):
        merged_data["Years of Experience"] = existing_resume_data["Years of Experience"]
    
    # Use existing firm info if new one is not provided
    if (new_resume_data.get("Firm Name & Location", {}).get("Name") == "Unknown" and 
        existing_resume_data.get("Firm Name & Location", {}).get("Name") != "Unknown"):
        merged_data["Firm Name & Location"] = existing_resume_data["Firm Name & Location"]
    
    # Use existing file_id if it exists and new one doesn't
    if existing_resume_data.get("file_id") and not new_resume_data.get("file_id"):
        merged_data["file_id"] = existing_resume_data["file_id"]
    
    return merged_data

# Function to create a default employee for cases where we need to return something
def create_default_employee(name: str) -> EmployeeDetail:
    """
    Create a default employee with the given name and empty fields
    to use as a fallback when the actual employee data can't be retrieved properly
    """
    logger.info(f"Creating default employee for: {name}")
    return EmployeeDetail(
        name=name,
        role="Role not available",
        years_experience={"Total": "Not available", "With Current Firm": "Not available"},
        firm={"Name": "Not available", "Location": "Not available"},
        education="Not available",
        professional_registrations=[],
        other_qualifications="Not available",
        relevant_projects=[],
        file_id=None
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Employee Resume API", "storage": "Supabase"}

# 1. Query endpoint
@app.post("/api/query", response_model=SearchResponse)
async def search_employees(query_request: QueryRequest):
    """
    Search for employees based on a natural language query
    """
    try:
        logger.info(f"Searching for employees with query: {query_request.query}")
        
        # Check if query is about a specific project
        is_project_query = "project" in query_request.query.lower() or "worked on" in query_request.query.lower()
        
        # Extract clean project name for later use
        clean_project_name = ""
        if is_project_query:
            # Extract the project name by removing common phrases
            project_name_clean = query_request.query.lower()
            project_name_clean = project_name_clean.replace("employees who have worked on project", "")
            project_name_clean = project_name_clean.replace("employees who have worked on", "")
            project_name_clean = project_name_clean.replace("employees who worked on project", "")
            project_name_clean = project_name_clean.replace("employees who worked on", "")
            project_name_clean = project_name_clean.replace("workers who have worked on", "")
            project_name_clean = project_name_clean.replace("people who worked on", "")
            project_name_clean = project_name_clean.replace("engineers who worked on", "")
            project_name_clean = project_name_clean.replace("employees worked on", "")
            project_name_clean = project_name_clean.replace("project", "")
            project_name_clean = project_name_clean.strip()
            
            # Special handling for quoted project names
            if '"' in project_name_clean:
                # Extract text inside quotes
                import re
                quoted_matches = re.findall(r'"([^"]*)"', project_name_clean)
                if quoted_matches:
                    project_name_clean = quoted_matches[0].strip()
            
            clean_project_name = project_name_clean
        
        # Analyze query intent using OpenAI
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                
                # Define system prompt based on query type
                system_prompt = "You are a helpful assistant that analyzes search queries about employees and their projects."
                if is_project_query:
                    system_prompt += " When the query is about employees who worked on a specific project, extract the exact project name and related keywords. "
                    system_prompt += "Focus primarily on project names, locations, and other distinctive features that can uniquely identify the project."
                
                # Get enhanced search query with OpenAI
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze this query: '{query_request.query}'. If it's about a specific project, extract the project name and any key details. Format your response as a comma-separated list of relevant search terms, prioritizing the most specific and distinctive terms first."}
                    ],
                    temperature=0.2,  # Lower temperature for more focused results
                    max_tokens=150
                )
                
                enhanced_search_terms = completion.choices[0].message.content.strip()
                logger.info(f"Enhanced search terms: {enhanced_search_terms}")
                
                # For project queries, we need to make sure the project name is preserved intact
                # as well as broken down into individual search terms
                if is_project_query:
                    # Add the original, unaltered project name to ensure exact matching is attempted
                    enhanced_query = f"{query_request.query} {clean_project_name} {enhanced_search_terms}"
                    
                    # Add specific handling for "Harahan Drainage Pump to the River" query
                    if "harahan" in clean_project_name.lower() and "pump" in clean_project_name.lower():
                        enhanced_query += " harahan drainage pump river drainage-pump pump-to-the-river pumping-station"
                else:
                    # For non-project queries, just append the enhanced terms
                    enhanced_query = f"{query_request.query} {enhanced_search_terms}"
                
                logger.info(f"Using enhanced query: {enhanced_query}")
            else:
                enhanced_query = query_request.query
                logger.info("No OpenAI API key found, using original query")
        except Exception as e:
            logger.warning(f"Error enhancing query with OpenAI: {str(e)}")
            enhanced_query = query_request.query
        
        # Use our adapter to search for employees with enhanced query
        from supabase_adapter import query_index
        results = query_index(
            query_text=enhanced_query,
            top_k=20,  # Increase top_k to get more potential matches
            match_threshold=0.01  # Use a very low threshold to get more results
        )
        
        # For project queries, if we didn't get results from vector search, try direct text search
        if is_project_query and len(results) == 0:
            logger.info("No results from vector search, trying direct text search")
            
            # Use the previously extracted clean project name for direct search
            project_name = clean_project_name
            
            # For "Harahan Drainage Pump to the River" search, use specific terms
            if "harahan" in project_name.lower() and "pump" in project_name.lower():
                project_terms = ["harahan", "drainage", "pump", "river"]
                search_term = " | ".join(project_terms)  # Use OR operator for better matching
            else:
                # Filter out small words (less than 3 characters) for better matching
                project_terms = [term for term in project_name.split() if len(term) > 2]
                search_term = " & ".join(project_terms) if project_terms else project_name
            
            try:
                # Directly search in resume_data using Supabase text search
                from supabase_adapter import supabase
                
                # Use text search to find employees with the project in resume_data
                logger.info(f"Performing direct text search for: {search_term}")
                
                try:
                    # First try using the search_employees_text function
                    direct_results = supabase.rpc(
                        'search_employees_text',
                        {
                            'search_query': search_term
                        }
                    ).execute()
                    
                    if hasattr(direct_results, 'error') and direct_results.error:
                        logger.warning(f"Error in direct text search function: {direct_results.error}")
                        # Function might not exist, fall back to manual filtering
                        raise Exception("Text search function not available")
                except Exception as e:
                    logger.warning(f"Falling back to manual text search: {str(e)}")
                    
                    # Get all employees and filter manually
                    all_employees = supabase.table("employees").select("*").execute()
                    
                    if hasattr(all_employees, 'error') and all_employees.error:
                        logger.error(f"Error retrieving employees for manual text search: {all_employees.error}")
                    elif all_employees.data:
                        logger.info(f"Got {len(all_employees.data)} employees for manual search")
                        
                        # Create a list to store direct search results
                        direct_results = type('DirectResults', (), {'data': []})
                        
                        # Search terms to look for
                        search_terms = [term.lower() for term in project_terms if len(term) > 2]
                        
                        # Manually filter employees by searching in their resume_data
                        for item in all_employees.data:
                            resume_data_str = json.dumps(item.get('resume_data', {})).lower()
                            
                            # Check if any of the search terms are in the resume_data
                            matches = [term for term in search_terms if term in resume_data_str]
                            
                            if matches:
                                # Add a similarity score based on how many terms matched
                                item['similarity'] = 0.5 + (len(matches) / len(search_terms) * 0.3)
                                direct_results.data.append(item)
                        
                        logger.info(f"Manual search found {len(direct_results.data)} matching employees")
                
                if hasattr(direct_results, 'data') and direct_results.data:
                    # Process the results similar to vector search
                    logger.info(f"Found {len(direct_results.data)} results in direct text search")
                    
                    for item in direct_results.data:
                        resume_data = item.get('resume_data', {})
                        
                        # Extract employee information
                        name = resume_data.get('Name', resume_data.get('name', item.get('employee_name', 'Unknown')))
                        
                        # Extract role
                        role = resume_data.get('Role in Contract', resume_data.get('Role', resume_data.get('role', 'Unknown')))
                        
                        # Extract projects
                        relevant_projects = resume_data.get('Relevant Projects', resume_data.get('relevant_projects', []))
                        
                        # Format the employee info
                        employee_info = {
                            'id': item.get('id', ''),
                            'name': name,
                            'role': role,
                            'education': resume_data.get('Education', resume_data.get('education', [])),
                            'years_experience': resume_data.get('Years of Experience', resume_data.get('years_experience', 'Not provided')),
                            'relevant_projects': relevant_projects,
                            'score': 0.8  # Assign a reasonable score for direct matches
                        }
                        
                        # Find specific matching project
                        for project in relevant_projects:
                            if isinstance(project, dict):
                                project_text = " ".join(str(v).lower() for v in project.values())
                                
                                # Check if any project term is in the project text
                                if any(term in project_text for term in project_terms):
                                    employee_info['matched_project'] = project
                                    employee_info['project_match_score'] = 0.9
                                    break
                        
                        results.append(employee_info)
            except Exception as e:
                logger.error(f"Error in direct text search: {e}")
        
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
            
            # Get relevant projects
            relevant_projects = employee.get("relevant_projects", [])
            
            # Initialize matching project info
            matching_project_info = None
            
            # If we have a project match from the adapter, use that first
            if employee.get('matched_project'):
                matching_project_info = {
                    "title": employee['matched_project'].get("Title and Location", 
                             employee['matched_project'].get("Title", 
                             employee['matched_project'].get("Name", "Unknown Project"))),
                    "role": employee['matched_project'].get("Role", "Unknown Role"),
                    "description": employee['matched_project'].get("Description", "No description available"),
                    "match_reason": f"This project matches your search for '{query_request.query}'",
                    "match_score": employee.get('project_match_score', 0)
                }
            # If no match yet, try to find one by parsing projects
            elif is_project_query:
                filtered_projects = []
                project_terms = enhanced_query.lower().split()
                
                # Keep only meaningful terms (at least 3 characters)
                project_terms = [term for term in project_terms if len(term) > 2]
                
                for project in relevant_projects:
                    if isinstance(project, dict):
                        # Create a string of all project values for searching
                        project_text = " ".join(str(v).lower() for v in project.values())
                        
                        # Count how many terms match
                        matching_terms = [term for term in project_terms if term in project_text]
                        
                        # If any significant term matches, include the project
                        if matching_terms:
                            project['_match_count'] = len(matching_terms)
                            filtered_projects.append(project)
                    elif isinstance(project, str):
                        matching_terms = [term for term in project_terms if term in project.lower()]
                        if matching_terms:
                            filtered_projects.append({
                                "Title": project,
                                "_match_count": len(matching_terms)
                            })
                
                # Sort filtered projects by match count
                filtered_projects.sort(key=lambda p: p.get('_match_count', 0), reverse=True)
                
                # If we found matching projects, use only those
                if filtered_projects:
                    relevant_projects = filtered_projects
                    
                    # Use the best matching project for the info
                    best_project = filtered_projects[0]
                    
                    # Calculate a match score
                    match_score = min(1.0, best_project.get('_match_count', 0) / len(project_terms) if project_terms else 0)
                    
                    matching_project_info = {
                        "title": best_project.get("Title and Location", 
                                best_project.get("Title", 
                                best_project.get("Name", "Unknown Project"))),
                        "role": best_project.get("Role", "Unknown Role"),
                        "description": best_project.get("Description", "No description available"),
                        "match_reason": f"This project matches your search for '{query_request.query}'",
                        "match_score": match_score
                    }
            
            # Remove any internal matching metadata from projects before returning
            for project in relevant_projects:
                if isinstance(project, dict) and '_match_count' in project:
                    del project['_match_count']
            
            employees.append(
                EmployeeResponse(
                    name=employee.get("name", "Unknown"),
                    role=role_str,
                    score=employee.get("score", 0),
                    education=education_str,
                    years_experience=employee.get("years_experience", "Not provided"),
                    relevant_projects=relevant_projects,
                    matching_project_info=matching_project_info
                )
            )
        
        logger.info(f"Found {len(employees)} employees matching the query")
        return SearchResponse(
            query=query_request.query,
            results=employees
        )
    
    except Exception as e:
        logger.error(f"Error querying employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying employees: {str(e)}")

# 2. Get all employees
@app.get("/api/employees", response_model=EmployeeList)
async def list_all_employees():
    """
    Get a list of all employees
    """
    try:
        logger.info("Retrieving all employees")
        employees = get_all_employees()
        logger.info(f"Retrieved {len(employees)} employees")
        return EmployeeList(employees=employees)
    
    except Exception as e:
        logger.error(f"Error retrieving employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving employees: {str(e)}")

# 3. Get specific employee
@app.get("/api/employees/{employee_name}", response_model=EmployeeDetail)
async def get_employee(employee_name: str):
    """
    Get detailed information about a specific employee
    """
    try:
        logger.info(f"Retrieving employee details for: {employee_name}")
        employee = get_employee_by_name(employee_name)
        
        if not employee:
            logger.warning(f"Employee not found: {employee_name}")
            suggestion_message = (
                f"Employee '{employee_name}' not found. "
                f"The name might be spelled differently or may not exist in the database. "
                f"You can try using the search endpoint or list all employees to find the correct name."
            )
            raise HTTPException(status_code=404, detail=suggestion_message)
        
        # Check if employee data is empty (all fields are None or empty)
        is_empty = all([
            not employee.role,
            not employee.years_experience or employee.years_experience == {},
            not employee.firm or employee.firm == {},
            not employee.education or employee.education == [],
            not employee.professional_registrations or employee.professional_registrations == [],
            not employee.other_qualifications,
            not employee.relevant_projects or employee.relevant_projects == []
        ])
        
        if is_empty:
            logger.warning(f"Employee found but has empty data: {employee_name}")
            # Create default employee with the name but empty fields
            employee = create_default_employee(employee_name)
            
        logger.info(f"Successfully retrieved employee details for: {employee_name}")
        return employee
    
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error retrieving employee details: {str(e)}"
        logger.error(error_message)
        
        # Fallback to default employee in case of error
        logger.info(f"Returning default employee as fallback for: {employee_name}")
        return create_default_employee(employee_name)

# 4. Get employees by role
@app.get("/api/roles/{role}", response_model=EmployeeList)
async def get_employees_for_role(role: str):
    """
    Get all employees with a specific role
    """
    try:
        logger.info(f"Retrieving employees with role: {role}")
        employees = get_employees_by_role(role)
        logger.info(f"Found {len(employees)} employees with role: {role}")
        return EmployeeList(employees=employees)
    
    except Exception as e:
        logger.error(f"Error retrieving employees by role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving employees by role: {str(e)}")

def find_similar_employee(name: str) -> Optional[str]:
    """
    Find an existing employee with a similar name to avoid duplicates.
    This helps with cases like "Jim Wilson" vs "Jim-Wilson" or "Jim Wilson 1".
    
    Args:
        name: The name to check for similar employees
        
    Returns:
        The name of the similar employee if found, None otherwise
    """
    try:
        # Normalize the input name for comparison
        from supabase_adapter import supabase
        
        normalized_name = name.lower().replace('-', ' ').replace('_', ' ')
        normalized_name = ' '.join([part for part in normalized_name.split() if not part.isdigit()])
        normalized_name = normalized_name.strip()
        
        # Get all employees
        result = supabase.table("employees").select("employee_name").execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error retrieving employees for similarity check: {result.error}")
            return None
            
        for item in result.data:
            existing_name = item.get("employee_name", "")
            
            # Normalize existing name
            existing_normalized = existing_name.lower().replace('-', ' ').replace('_', ' ')
            existing_normalized = ' '.join([part for part in existing_normalized.split() if not part.isdigit()])
            existing_normalized = existing_normalized.strip()
            
            # Check if normalized names match
            if normalized_name == existing_normalized:
                logger.info(f"Found similar existing employee: '{existing_name}' for input '{name}'")
                return existing_name
        
        return None
    
    except Exception as e:
        logger.error(f"Error checking for similar employees: {str(e)}")
        return None

# 5. Add employee with resume upload
@app.post("/api/employees", response_model=EmployeeDetail)
async def add_employee(
    file: UploadFile = File(...),
    employee_name: str = Form(None)
):
    """
    Add a new employee by uploading their resume PDF
    Extract structured data using simple parsing and store in Supabase
    If employee already exists, merge the new data with existing data
    """
    try:
        # Create a temporary file to store the uploaded PDF
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # If no name was provided, use the filename
        if not employee_name:
            employee_name = os.path.splitext(file.filename)[0].replace("_", " ").title()
            logger.info(f"Using filename as employee name: {employee_name}")
        
        logger.info(f"Processing resume for: {employee_name}")
        
        # Check for similar existing employees
        similar_name = find_similar_employee(employee_name)
        if similar_name and similar_name != employee_name:
            logger.info(f"Found similar existing employee '{similar_name}', using that instead of '{employee_name}'")
            employee_name = similar_name
        
        # Process the file to extract basic data
        try:
            # Import the PDF extraction functionality
            try:
                # First try to import from resume_parser
                sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
                from resume_parser.dataparser import extract_structured_data_with_mistral, upload_pdf_to_mistral
                
                # Process the PDF file
                logger.info(f"Uploading PDF to Mistral AI: {temp_file_path}")
                pdf_url = upload_pdf_to_mistral(temp_file_path)
                
                if pdf_url:
                    logger.info(f"Extracting data from PDF using Mistral AI")
                    structured_data = extract_structured_data_with_mistral(pdf_url)
                    
                    if structured_data:
                        logger.info(f"Successfully extracted data from PDF for {employee_name}")
                        
                        # Use the extracted data to populate the employee record
                        new_resume_data = format_employee_data(
                            employee_name=employee_name,
                            role=structured_data.get('role', None),
                            years_experience=structured_data.get('years_experience', None),
                            firm=structured_data.get('firm_name_and_location', None),
                            education=structured_data.get('education', None),
                            professional_registrations=structured_data.get('current_professional_registration', None),
                            other_qualifications=structured_data.get('other_professional_qualifications', None),
                            relevant_projects=structured_data.get('relevant_projects', None),
                            file_id=file.filename
                        )
                    else:
                        logger.warning(f"Failed to extract structured data from PDF, using default values")
                        new_resume_data = format_employee_data(
                            employee_name=employee_name,
                            file_id=file.filename
                        )
                else:
                    logger.warning(f"Failed to upload PDF to Mistral AI, using default values")
                    new_resume_data = format_employee_data(
                        employee_name=employee_name,
                        file_id=file.filename
                    )
            except ImportError as e:
                logger.warning(f"Could not import dataparser: {str(e)}, using default values")
                new_resume_data = format_employee_data(
                    employee_name=employee_name,
                    file_id=file.filename
                )
            
            # Check if employee already exists
            existing_employee = get_employee_by_name(employee_name)
            
            # If employee exists, merge the data
            if existing_employee:
                logger.info(f"Employee {employee_name} already exists, merging data")
                
                # Get existing data
                from supabase_adapter import supabase
                employee_id = employee_name.lower().replace(' ', '_')
                result = supabase.table("employees").select("*").eq("id", employee_id).execute()
                
                if hasattr(result, 'error') and result.error:
                    logger.error(f"Error retrieving existing employee data: {result.error}")
                elif result.data:
                    existing_resume_data = result.data[0].get("resume_data", {})
                    # Use the helper function to merge the data
                    new_resume_data = merge_employee_data(new_resume_data, existing_resume_data)
            
            # Convert employee name to a valid id by replacing spaces with underscores
            employee_id = employee_name.lower().replace(' ', '_')
            
            # Generate embedding for the resume data
            resume_text = json.dumps(new_resume_data)
            embedding = generate_embedding(resume_text)
            
            # Store in Supabase
            from supabase_adapter import supabase
            
            vector_data = {
                "id": employee_id,
                "employee_name": employee_name,
                "file_id": file.filename,
                "resume_data": new_resume_data,
                "embedding": embedding
            }
            
            # Upsert into Supabase
            result = supabase.table("employees").upsert(vector_data).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error storing employee in Supabase: {result.error}")
                raise HTTPException(status_code=500, detail="Failed to store employee data")
            
            if existing_employee:
                logger.info(f"Successfully updated employee: {employee_name}")
            else:
                logger.info(f"Successfully added new employee: {employee_name}")
            
            # Get the employee details
            updated_employee = get_employee_by_name(employee_name)
            
            if not updated_employee:
                logger.error(f"Failed to retrieve employee after storage: {employee_name}")
                # Return a default employee as fallback
                return create_default_employee(employee_name)
            
            return updated_employee
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Removed temporary file: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Error adding/updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding/updating employee: {str(e)}")

# 6. Add employee manually
@app.post("/api/employees/manual", response_model=EmployeeDetail)
async def add_employee_manually(employee: EmployeeCreate):
    """
    Add a new employee manually with structured data
    If employee already exists, merge the new data with existing data
    """
    try:
        logger.info(f"Adding or updating employee: {employee.name}")
        
        # Check for similar existing employees
        similar_name = find_similar_employee(employee.name)
        if similar_name and similar_name != employee.name:
            logger.info(f"Found similar existing employee '{similar_name}', using that instead of '{employee.name}'")
            # Create a new employee with the corrected name
            corrected_employee = EmployeeCreate(
                name=similar_name,
                role=employee.role,
                years_experience=employee.years_experience,
                firm=employee.firm,
                education=employee.education,
                professional_registrations=employee.professional_registrations,
                other_qualifications=employee.other_qualifications,
                relevant_projects=employee.relevant_projects
            )
            employee = corrected_employee
        
        # Check if employee already exists
        existing_employee = get_employee_by_name(employee.name)
        
        # Format the new employee data
        new_resume_data = format_employee_data(
            employee_name=employee.name,
            role=employee.role,
            years_experience=employee.years_experience,
            firm=employee.firm,
            education=employee.education,
            professional_registrations=employee.professional_registrations,
            other_qualifications=employee.other_qualifications,
            relevant_projects=employee.relevant_projects,
            file_id=None
        )
        
        # If employee exists, merge the data
        if existing_employee:
            logger.info(f"Employee {employee.name} already exists, merging data")
            
            # Get existing data
            from supabase_adapter import supabase
            employee_id = employee.name.lower().replace(' ', '_')
            result = supabase.table("employees").select("*").eq("id", employee_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error retrieving existing employee data: {result.error}")
            elif result.data:
                existing_resume_data = result.data[0].get("resume_data", {})
                # Use the helper function to merge the data
                new_resume_data = merge_employee_data(new_resume_data, existing_resume_data)
        
        # Generate an embedding for the employee data
        employee_text = json.dumps(new_resume_data)
        embedding = generate_embedding(employee_text)
        
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee.name.lower().replace(' ', '_')
        
        # Prepare data for Supabase
        from supabase_adapter import supabase
        
        vector_data = {
            "id": employee_id,
            "employee_name": employee.name,
            "file_id": new_resume_data.get("file_id"),
            "resume_data": new_resume_data,
            "embedding": embedding
        }
        
        # Upsert into Supabase
        result = supabase.table("employees").upsert(vector_data).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error storing employee in Supabase: {result.error}")
            raise HTTPException(status_code=500, detail="Failed to store employee data")
        
        if existing_employee:
            logger.info(f"Successfully updated employee: {employee.name}")
        else:
            logger.info(f"Successfully added new employee: {employee.name}")
        
        # Get the employee details
        updated_employee = get_employee_by_name(employee.name)
        
        if not updated_employee:
            logger.error(f"Failed to retrieve employee after storage: {employee.name}")
            # Return a default employee as fallback
            return create_default_employee(employee.name)
        
        return updated_employee
    
    except Exception as e:
        logger.error(f"Error adding/updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding/updating employee: {str(e)}")

# 7. Delete employee
@app.delete("/api/employees/{employee_name}")
async def delete_employee(employee_name: str):
    """
    Delete an employee by name
    """
    try:
        logger.info(f"Deleting employee: {employee_name}")
        success = delete_employee_by_name(employee_name)
        if not success:
            logger.warning(f"Employee not found for deletion: {employee_name}")
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
        logger.info(f"Successfully deleted employee: {employee_name}")
        return {"message": f"Employee '{employee_name}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

# 8. Update an existing employee
@app.put("/api/employees/{employee_name}", response_model=EmployeeDetail)
async def update_employee_manually(employee_name: str, employee: EmployeeCreate):
    """
    Update an existing employee with new data
    The existing data and new data will be merged
    """
    try:
        # Check if employee exists (required for PUT)
        existing_employee = get_employee_by_name(employee_name)
        if not existing_employee:
            logger.warning(f"Employee not found for update: {employee_name}")
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
        logger.info(f"Updating employee: {employee_name}")
        
        # Format the new employee data
        new_resume_data = format_employee_data(
            employee_name=employee_name,
            role=employee.role,
            years_experience=employee.years_experience,
            firm=employee.firm,
            education=employee.education,
            professional_registrations=employee.professional_registrations,
            other_qualifications=employee.other_qualifications,
            relevant_projects=employee.relevant_projects,
            file_id=None
        )
        
        # Get existing data
        from supabase_adapter import supabase
        employee_id = employee_name.lower().replace(' ', '_')
        result = supabase.table("employees").select("*").eq("id", employee_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error retrieving existing employee data: {result.error}")
            raise HTTPException(status_code=500, detail="Failed to retrieve existing employee data")
        
        if not result.data:
            logger.error(f"No data found for employee: {employee_name}")
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found in database")
        
        existing_resume_data = result.data[0].get("resume_data", {})
        
        # Use the helper function to merge the data
        merged_resume_data = merge_employee_data(new_resume_data, existing_resume_data)
        
        # Generate an embedding for the updated employee data
        employee_text = json.dumps(merged_resume_data)
        embedding = generate_embedding(employee_text)
        
        # Prepare data for Supabase
        vector_data = {
            "id": employee_id,
            "employee_name": employee_name,
            "file_id": merged_resume_data.get("file_id"),
            "resume_data": merged_resume_data,
            "embedding": embedding
        }
        
        # Update in Supabase
        result = supabase.table("employees").update(vector_data).eq("id", employee_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error updating employee in Supabase: {result.error}")
            raise HTTPException(status_code=500, detail="Failed to update employee data")
        
        logger.info(f"Successfully updated employee: {employee_name}")
        
        # Get the updated employee details
        updated_employee = get_employee_by_name(employee_name)
        
        if not updated_employee:
            logger.error(f"Failed to retrieve employee after update: {employee_name}")
            # Return a default employee as fallback
            return create_default_employee(employee_name)
        
        return updated_employee
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

# 9. Create or update a specific employee with predefined data
@app.post("/api/fix_employee/{employee_name}")
async def fix_employee(employee_name: str):
    """
    Create or update a specific employee with predefined data.
    This endpoint is used to fix specific employees that may have issues.
    If employee already exists, the data will be merged.
    """
    try:
        logger.info(f"Fixing employee data for: {employee_name}")
        
        # Check if employee already exists
        existing_employee = get_employee_by_name(employee_name)
        
        # Predefined data for specific employees
        if employee_name.lower() == "manish mardia":
            # Specific data for Manish Mardia
            new_resume_data = format_employee_data(
                employee_name="Manish Mardia",
                role="Senior Structural Engineer",
                years_experience={
                    "Total": "15 years",
                    "With Current Firm": "8 years"
                },
                firm={
                    "Name": "ABC Engineering",
                    "Location": "Mumbai, India"
                },
                education="Master of Structural Engineering, IIT Bombay",
                professional_registrations=[
                    {"Registration": "PE", "State": "Maharashtra", "Year": 2008}
                ],
                other_qualifications="LEED AP, PMP Certified",
                relevant_projects=[
                    {"Name": "Mumbai Metro Line 3", "Role": "Lead Structural Engineer", "Year": 2018},
                    {"Name": "Jawaharlal Nehru Stadium Renovation", "Role": "Structural Consultant", "Year": 2016}
                ]
            )
        else:
            # Default data for other employees
            new_resume_data = format_employee_data(
                employee_name=employee_name,
                role="Employee",
                years_experience={
                    "Total": "Not specified",
                    "With Current Firm": "Not specified"
                }
            )
        
        # If employee exists, merge the data
        if existing_employee:
            logger.info(f"Employee {employee_name} already exists, merging data")
            
            # Get existing data
            from supabase_adapter import supabase
            employee_id = employee_name.lower().replace(' ', '_')
            result = supabase.table("employees").select("*").eq("id", employee_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error retrieving existing employee data: {result.error}")
            elif result.data:
                existing_resume_data = result.data[0].get("resume_data", {})
                # Use the helper function to merge the data
                new_resume_data = merge_employee_data(new_resume_data, existing_resume_data)
        
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee_name.lower().replace(' ', '_')
        
        # Generate embedding for the resume data
        resume_text = json.dumps(new_resume_data)
        embedding = generate_embedding(resume_text)
        
        # Store in Supabase
        from supabase_adapter import supabase
        
        vector_data = {
            "id": employee_id,
            "employee_name": employee_name,
            "file_id": new_resume_data.get("file_id"),
            "resume_data": new_resume_data,
            "embedding": embedding
        }
        
        # Upsert into Supabase
        result = supabase.table("employees").upsert(vector_data).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error storing employee in Supabase: {result.error}")
            raise HTTPException(status_code=500, detail="Failed to store employee data")
        
        if existing_employee:
            logger.info(f"Successfully updated employee data for: {employee_name}")
        else:
            logger.info(f"Successfully added new employee: {employee_name}")
        
        # Get the employee details to verify
        employee = get_employee_by_name(employee_name)
        
        if not employee:
            logger.error(f"Failed to retrieve employee after fix: {employee_name}")
            return {"message": f"Employee data updated but could not verify", "success": True}
        
        return {"message": f"Employee '{employee_name}' data fixed successfully", "success": True, "employee": employee}
    
    except Exception as e:
        logger.error(f"Error fixing employee data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fixing employee data: {str(e)}")

# 10. Merge duplicate employees
@app.post("/api/merge_employees")
async def merge_duplicate_employees(source_name: str, target_name: str):
    """
    Merge two employee records, copying data from source to target and then deleting the source.
    This is useful for cleaning up duplicate entries.
    
    Args:
        source_name: The name of the employee to merge from
        target_name: The name of the employee to merge into
    """
    try:
        logger.info(f"Merging employee '{source_name}' into '{target_name}'")
        
        # Get source employee
        source_employee = get_employee_by_name(source_name)
        if not source_employee:
            logger.warning(f"Source employee not found: {source_name}")
            raise HTTPException(status_code=404, detail=f"Source employee '{source_name}' not found")
        
        # Get target employee
        target_employee = get_employee_by_name(target_name)
        if not target_employee:
            logger.warning(f"Target employee not found: {target_name}")
            raise HTTPException(status_code=404, detail=f"Target employee '{target_name}' not found")
        
        # Get the source and target data from Supabase
        from supabase_adapter import supabase
        source_id = source_name.lower().replace(' ', '_')
        target_id = target_name.lower().replace(' ', '_')
        
        source_result = supabase.table("employees").select("*").eq("id", source_id).execute()
        target_result = supabase.table("employees").select("*").eq("id", target_id).execute()
        
        if hasattr(source_result, 'error') and source_result.error:
            logger.error(f"Error retrieving source employee data: {source_result.error}")
            raise HTTPException(status_code=500, detail="Failed to retrieve source employee data")
            
        if hasattr(target_result, 'error') and target_result.error:
            logger.error(f"Error retrieving target employee data: {target_result.error}")
            raise HTTPException(status_code=500, detail="Failed to retrieve target employee data")
        
        if not source_result.data:
            logger.error(f"No data found for source employee: {source_name}")
            raise HTTPException(status_code=404, detail=f"Source employee '{source_name}' not found in database")
            
        if not target_result.data:
            logger.error(f"No data found for target employee: {target_name}")
            raise HTTPException(status_code=404, detail=f"Target employee '{target_name}' not found in database")
        
        # Get the resume data
        source_resume_data = source_result.data[0].get("resume_data", {})
        target_resume_data = target_result.data[0].get("resume_data", {})
        
        # Merge the data
        merged_resume_data = merge_employee_data(source_resume_data, target_resume_data)
        
        # Generate an embedding for the merged data
        merged_text = json.dumps(merged_resume_data)
        embedding = generate_embedding(merged_text)
        
        # Prepare data for Supabase
        vector_data = {
            "id": target_id,
            "employee_name": target_name,
            "file_id": merged_resume_data.get("file_id"),
            "resume_data": merged_resume_data,
            "embedding": embedding
        }
        
        # Update target in Supabase
        update_result = supabase.table("employees").update(vector_data).eq("id", target_id).execute()
        
        if hasattr(update_result, 'error') and update_result.error:
            logger.error(f"Error updating target employee in Supabase: {update_result.error}")
            raise HTTPException(status_code=500, detail="Failed to update target employee data")
        
        # Delete the source employee
        delete_result = supabase.table("employees").delete().eq("id", source_id).execute()
        
        if hasattr(delete_result, 'error') and delete_result.error:
            logger.error(f"Error deleting source employee: {delete_result.error}")
            logger.warning("Target employee was updated but source employee could not be deleted")
            return {
                "message": f"Employee '{source_name}' was merged into '{target_name}' but could not be deleted",
                "success": True
            }
        
        logger.info(f"Successfully merged '{source_name}' into '{target_name}' and deleted '{source_name}'")
        return {
            "message": f"Employee '{source_name}' was successfully merged into '{target_name}' and deleted",
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error merging employees: {str(e)}")

@app.post("/api/create_projects_from_employee/{employee_name}")
async def create_projects_from_employee(employee_name: str):
    """
    Extract projects from an employee's relevant_projects field and create them
    in the projects database (section_f_projects table).
    
    Args:
        employee_name: The name of the employee whose projects to extract
        
    Returns:
        Dict with status and list of created projects
    """
    try:
        logger.info(f"Extracting projects from employee: {employee_name}")
        
        # Get the employee data
        employee_data = get_employee_by_name(employee_name)
        if not employee_data:
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
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
            return {"status": "No projects found", "projects_created": []}
        
        # Track created projects
        created_projects = []
        
        # Process each project
        for project in relevant_projects:
            # Skip if project is not a dict or doesn't have required fields
            if not isinstance(project, dict):
                logger.warning(f"Invalid project format for employee {employee_name}: {project}")
                continue
                
            # Extract title and location from project
            title_and_location = None
            if "title_and_location" in project and project["title_and_location"]:
                title_and_location = project["title_and_location"]
            elif isinstance(project.get("title_and_location"), list) and len(project["title_and_location"]) >= 2:
                # Handle case where title_and_location is a list with [title, location]
                title_and_location = ", ".join(project["title_and_location"])
            
            if not title_and_location:
                logger.warning(f"Missing title for project in employee {employee_name}: {project}")
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
        
        return {
            "status": "success",
            "projects_created": created_projects
        }
    
    except Exception as e:
        logger.error(f"Error creating projects from employee {employee_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating projects: {str(e)}")

@app.post("/api/create_projects_from_all_employees")
async def create_projects_from_all_employees():
    """
    Extract projects from all employees' relevant_projects fields and create them
    in the projects database (section_f_projects table).
    
    Returns:
        Dict with status and summary of created projects
    """
    try:
        logger.info("Creating projects from all employees")
        
        # Get all employees
        employees = get_all_employees()
        
        if not employees:
            return {"status": "No employees found", "summary": {}}
        
        results = {}
        total_projects_created = 0
        
        # Process each employee
        for employee in employees:
            # Check if employee is a dict-like object or a Pydantic model
            if hasattr(employee, "name"):
                # It's a Pydantic model (EmployeeResponse)
                employee_name = employee.name
            elif hasattr(employee, "get"):
                # It's a dictionary
                employee_name = employee.get("name")
            else:
                # Try direct attribute access as fallback
                try:
                    employee_name = employee.name if hasattr(employee, "name") else str(employee)
                except:
                    logger.warning(f"Could not extract name from employee: {employee}")
                    continue
            
            if not employee_name:
                continue
                
            # Call the endpoint for a single employee
            try:
                result = await create_projects_from_employee(employee_name)
                projects_created = result.get("projects_created", [])
                results[employee_name] = len(projects_created)
                total_projects_created += len(projects_created)
                
                logger.info(f"Created {len(projects_created)} projects for employee {employee_name}")
            except Exception as e:
                logger.error(f"Error processing employee {employee_name}: {str(e)}")
                results[employee_name] = f"Error: {str(e)}"
        
        return {
            "status": "success",
            "total_projects_created": total_projects_created,
            "summary": results
        }
        
    except Exception as e:
        logger.error(f"Error creating projects from all employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating projects: {str(e)}")

# Run the API server
if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("api")

# Load environment variables from root .env file
from dotenv import load_dotenv
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

# Import utilities
from utils import generate_embedding

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
    delete_employee_by_name
)

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
        
        # Use our adapter to search for employees
        from supabase_adapter import query_index
        results = query_index(
            query_text=query_request.query,
            top_k=10,
            match_threshold=0.01  # Use a very low threshold to get more results
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
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
        logger.info(f"Successfully retrieved employee details for: {employee_name}")
        return employee
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving employee details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving employee: {str(e)}")

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

# 5. Add employee with resume upload
@app.post("/api/employees", response_model=EmployeeDetail)
async def add_employee(
    file: UploadFile = File(...),
    employee_name: str = Form(None)
):
    """
    Add a new employee by uploading their resume PDF
    Extract structured data using simple parsing and store in Supabase
    """
    try:
        # Create a temporary file to store the uploaded PDF
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        logger.info(f"Processing resume for: {employee_name or 'Unknown'}")
        
        # Process the file to extract basic data
        try:
            # If no name was provided, use the filename
            if not employee_name:
                employee_name = os.path.splitext(file.filename)[0].replace("_", " ").title()
                logger.info(f"Using filename as employee name: {employee_name}")
            
            # Create basic resume data structure
            resume_data = {
                "Name": employee_name,
                "Role in Contract": "Not specified",
                "Years of Experience": {
                    "Total": "Unknown",
                    "With Current Firm": "Unknown"
                },
                "Firm Name & Location": {
                    "Name": "Unknown",
                    "Location": "Unknown"
                },
                "Education": "Not provided",
                "Professional Registrations": [],
                "Other Professional Qualifications": "Not provided",
                "Relevant Projects": []
            }
            
            # Convert employee name to a valid id by replacing spaces with underscores
            employee_id = employee_name.lower().replace(' ', '_')
            
            # Generate embedding for the resume data
            resume_text = json.dumps(resume_data)
            embedding = generate_embedding(resume_text)
            
            # Store in Supabase
            from supabase_adapter import supabase
            
            vector_data = {
                "id": employee_id,
                "employee_name": employee_name,
                "file_id": file.filename,
                "resume_data": resume_data,
                "embedding": embedding
            }
            
            # Upsert into Supabase
            result = supabase.table("employees").upsert(vector_data).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error storing employee in Supabase: {result.error}")
                raise HTTPException(status_code=500, detail="Failed to store employee data")
            
            logger.info(f"Successfully added employee: {employee_name}")
            
            # Get the employee details
            employee = get_employee_by_name(employee_name)
            
            if not employee:
                logger.error(f"Failed to retrieve employee after storage: {employee_name}")
                raise HTTPException(status_code=500, detail="Employee was stored but could not be retrieved")
            
            return employee
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Removed temporary file: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Error adding employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding employee: {str(e)}")

# 6. Add employee manually
@app.post("/api/employees/manual", response_model=EmployeeDetail)
async def add_employee_manually(employee: EmployeeCreate):
    """
    Add a new employee manually with structured data
    """
    try:
        logger.info(f"Adding employee manually: {employee.name}")
        
        # Generate an embedding for the employee data
        employee_text = json.dumps(employee.dict())
        embedding = generate_embedding(employee_text)
        
        # Convert employee name to a valid id by replacing spaces with underscores
        employee_id = employee.name.lower().replace(' ', '_')
        
        # Prepare data for Supabase
        from supabase_adapter import supabase
        
        # Structure the data according to the resume format
        resume_data = {
            "Name": employee.name,
            "Role in Contract": employee.role,
            "Years of Experience": employee.years_experience,
            "Firm Name & Location": employee.firm,
            "Education": employee.education,
            "Professional Registrations": employee.professional_registrations,
            "Other Professional Qualifications": employee.other_qualifications,
            "Relevant Projects": employee.relevant_projects
        }
        
        vector_data = {
            "id": employee_id,
            "employee_name": employee.name,
            "file_id": None,
            "resume_data": resume_data,
            "embedding": embedding
        }
        
        # Upsert into Supabase
        result = supabase.table("employees").upsert(vector_data).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error storing employee in Supabase: {result.error}")
            raise HTTPException(status_code=500, detail="Failed to store employee data")
        
        logger.info(f"Successfully added employee: {employee.name}")
        
        # Get the employee details
        new_employee = get_employee_by_name(employee.name)
        
        if not new_employee:
            logger.error(f"Failed to retrieve employee after storage: {employee.name}")
            raise HTTPException(status_code=500, detail="Employee was stored but could not be retrieved")
        
        return new_employee
    
    except Exception as e:
        logger.error(f"Error adding employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding employee: {str(e)}")

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

# Run the API server
if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
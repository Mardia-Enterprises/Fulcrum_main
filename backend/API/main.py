from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json

# Add parent directory to path to import from Resume_Parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions from Resume_Parser
from Resume_Parser.datauploader import query_employees, upsert_resume_in_pinecone, generate_embedding
from Resume_Parser.dataparser import upload_pdf_to_mistral, extract_structured_data_with_mistral

# Import models
from API.models import (
    QueryRequest, 
    EmployeeResponse, 
    EmployeeList, 
    EmployeeDetail,
    EmployeeCreate,
    SearchResponse
)

# Import database functions
from API.database import (
    get_all_employees,
    get_employee_by_name,
    get_employees_by_role,
    delete_employee_by_name
)

# Create FastAPI app
app = FastAPI(
    title="Employee Resume API",
    description="API for querying and managing employee resume data",
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
    return {"message": "Welcome to the Employee Resume API"}

# 1. Query endpoint
@app.post("/api/query", response_model=SearchResponse)
async def search_employees(query_request: QueryRequest):
    """
    Search for employees based on a natural language query
    """
    try:
        results = query_employees(query_request.query)
        
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
        
        return SearchResponse(
            query=query_request.query,
            results=employees
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying employees: {str(e)}")

# 2. Get all employees
@app.get("/api/employees", response_model=EmployeeList)
async def list_all_employees():
    """
    Get a list of all employees
    """
    try:
        employees = get_all_employees()
        return EmployeeList(employees=employees)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employees: {str(e)}")

# 3. Get specific employee
@app.get("/api/employees/{employee_name}", response_model=EmployeeDetail)
async def get_employee(employee_name: str):
    """
    Get detailed information about a specific employee
    """
    try:
        employee = get_employee_by_name(employee_name)
        if not employee:
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
        return employee
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employee: {str(e)}")

# 4. Get employees by role
@app.get("/api/roles/{role}", response_model=EmployeeList)
async def get_employees_for_role(role: str):
    """
    Get all employees with a specific role
    """
    try:
        employees = get_employees_by_role(role)
        return EmployeeList(employees=employees)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employees by role: {str(e)}")

# 5. Add employee (upload resume)
@app.post("/api/employees", response_model=EmployeeDetail)
async def add_employee(
    file: UploadFile = File(...),
    employee_name: str = Form(None)
):
    """
    Add a new employee by uploading their resume PDF
    """
    try:
        # Create a temporary file to store the uploaded PDF
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Process the PDF
        try:
            # Upload PDF to Mistral
            pdf_url = upload_pdf_to_mistral(temp_file_path)
            
            # Extract structured data
            structured_data = extract_structured_data_with_mistral(pdf_url)
            
            # Use provided name or extract from PDF
            if employee_name:
                structured_data["Name"] = employee_name
            else:
                employee_name = structured_data.get("Name", "Unknown")
            
            # Store in Pinecone
            upsert_resume_in_pinecone(employee_name, pdf_url, structured_data)
            
            # Get the employee details
            employee = get_employee_by_name(employee_name)
            
            return employee
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding employee: {str(e)}")

# 6. Delete employee
@app.delete("/api/employees/{employee_name}")
async def delete_employee(employee_name: str):
    """
    Delete an employee by name
    """
    try:
        success = delete_employee_by_name(employee_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Employee '{employee_name}' not found")
        
        return {"message": f"Employee '{employee_name}' deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

# Run the API server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
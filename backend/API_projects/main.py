from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json
import logging
import shutil
import uuid
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

# Import utilities first so we can use setup_logging
from .utils import generate_embedding, setup_logging

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

# Add resume_parser_f directory to path
resume_parser_f_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resume_parser_f"))
sys.path.append(resume_parser_f_dir)
from resume_parser_f.dataparser import extract_structured_data_with_mistral, upload_pdf_to_mistral, upsert_project_in_supabase

# Import models
from .models import (
    QueryRequest, 
    ProjectResponse, 
    ProjectList, 
    ProjectDetail,
    ProjectCreate,
    SearchResponse
)

# Import database functions
from .database import (
    get_all_projects,
    get_project_by_title,
    delete_project_by_title,
    format_project_data
)

# Import Supabase client for direct access
from .supabase_adapter import supabase

# Create FastAPI app
app = FastAPI(
    title="Project API",
    description="API for querying and managing project data stored in Supabase",
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

def merge_project_data(new_project_data: Dict[str, Any], existing_project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new project data with existing data, preserving existing information
    and appending new information as needed.
    
    Args:
        new_project_data: The new project data
        existing_project_data: The existing project data
        
    Returns:
        Dict[str, Any]: The merged project data
    """
    # Make a copy of the new data to avoid modifying the original
    merged_data = new_project_data.copy()
    
    # Use the more detailed title_and_location if provided
    if not new_project_data.get("title_and_location") and existing_project_data.get("title_and_location"):
        merged_data["title_and_location"] = existing_project_data["title_and_location"]
    
    # Use existing year_completed if new one is not provided
    if not new_project_data.get("year_completed") and existing_project_data.get("year_completed"):
        merged_data["year_completed"] = existing_project_data["year_completed"]
    
    # Use existing project_owner if new one is not provided
    if (new_project_data.get("project_owner") == "Not provided" and 
        existing_project_data.get("project_owner") != "Not provided"):
        merged_data["project_owner"] = existing_project_data["project_owner"]
    
    # Use existing point_of_contact_name if new one is not provided
    if (new_project_data.get("point_of_contact_name") == "Not provided" and 
        existing_project_data.get("point_of_contact_name") != "Not provided"):
        merged_data["point_of_contact_name"] = existing_project_data["point_of_contact_name"]
    
    # Use existing point_of_contact_telephone_number if new one is not provided
    if (new_project_data.get("point_of_contact_telephone_number") == "Not provided" and 
        existing_project_data.get("point_of_contact_telephone_number") != "Not provided"):
        merged_data["point_of_contact_telephone_number"] = existing_project_data["point_of_contact_telephone_number"]
    
    # Use the more detailed brief_description if provided
    if (new_project_data.get("brief_description") == "Not provided" and 
        existing_project_data.get("brief_description") != "Not provided"):
        merged_data["brief_description"] = existing_project_data["brief_description"]
    
    # Merge firms involved
    existing_firms = existing_project_data.get("firms_from_section_c_involved_with_this_project", [])
    new_firms = new_project_data.get("firms_from_section_c_involved_with_this_project", [])
    
    # Create a set of firm names to avoid duplicates
    existing_firm_names = set()
    for firm in existing_firms:
        if isinstance(firm, dict) and "firm_name" in firm:
            existing_firm_names.add(firm["firm_name"])
    
    # Add new firms that don't exist
    merged_firms = existing_firms.copy()
    for firm in new_firms:
        if isinstance(firm, dict) and "firm_name" in firm:
            if firm["firm_name"] not in existing_firm_names:
                merged_firms.append(firm)
    
    if merged_firms:
        merged_data["firms_from_section_c_involved_with_this_project"] = merged_firms
    
    # Use existing file_id if it exists and new one doesn't
    if existing_project_data.get("file_id") and not new_project_data.get("file_id"):
        merged_data["file_id"] = existing_project_data["file_id"]
    
    return merged_data

# Function to create a default project for cases where we need to return something
def create_default_project(title: str) -> ProjectDetail:
    """
    Create a default project with the given title and empty fields
    to use as a fallback when the actual project data can't be retrieved properly
    """
    logger.info(f"Creating default project for: {title}")
    return ProjectDetail(
        title_and_location=title,
        year_completed={"professional_services": None, "construction": None},
        project_owner="Not available",
        point_of_contact_name="Not available",
        point_of_contact_telephone_number="Not available",
        brief_description="Not available",
        firms_from_section_c_involved_with_this_project=[],
        file_id=None
    )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Project API", "storage": "Supabase"}

# 1. Query endpoint
@app.post("/api/query", response_model=SearchResponse)
async def search_projects(query_request: QueryRequest):
    """
    Search for projects based on a natural language query
    """
    try:
        logger.info(f"Searching for projects with query: {query_request.query}")
        
        # Analyze query intent using OpenAI
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = OpenAI(api_key=api_key)
                
                # Prepare query for semantic search
                query_text = query_request.query
                
                # Get search results from Supabase
                from .supabase_adapter import query_index
                
                # Search across both semantic vectors and text search
                search_results = query_index(query_text, top_k=20, match_threshold=0.01)
                
                # Convert results to API response format
                results = []
                for match in search_results:
                    project_data = match.get("project_data", {})
                    
                    # Check if project_data is a string
                    if isinstance(project_data, str):
                        try:
                            project_data = json.loads(project_data)
                        except Exception as e:
                            logger.error(f"Error parsing project data: {e}")
                            project_data = {}
                    
                    # Extract relevant fields for response
                    title_and_location = project_data.get("title_and_location", match.get("project_key", "Unknown Project"))
                    project_owner = project_data.get("project_owner", "Not provided")
                    brief_description = project_data.get("brief_description", "Not provided")
                    year_completed = project_data.get("year_completed", {})
                    similarity_score = match.get("similarity", 0.0)
                    
                    # Add to results
                    results.append(
                        ProjectResponse(
                            title_and_location=title_and_location,
                            project_owner=project_owner,
                            score=similarity_score,
                            year_completed=year_completed,
                            brief_description=brief_description
                        )
                    )
                
                # Sort results by score in descending order
                results.sort(key=lambda x: x.score, reverse=True)
                
                # Create final response
                return SearchResponse(
                    query=query_request.query,
                    results=results
                )
            else:
                # If no OpenAI key, perform a simple text search
                logger.warning("OpenAI key not set. Using simple text search only.")
                
                # Get projects directly from Supabase
                projects = get_all_projects()
                
                # Filter projects based on simple text matching
                keywords = query_request.query.lower().split()
                results = []
                
                for project in projects:
                    score = 0.0
                    title_lower = project.title_and_location.lower()
                    desc_lower = project.brief_description.lower() if project.brief_description else ""
                    
                    for keyword in keywords:
                        if keyword in title_lower:
                            score += 0.5
                        if keyword in desc_lower:
                            score += 0.2
                    
                    # Only include if there's some match
                    if score > 0:
                        project.score = min(score, 1.0)  # Normalize score
                        results.append(project)
                
                # Sort results by score in descending order
                results.sort(key=lambda x: x.score, reverse=True)
                
                # Create final response
                return SearchResponse(
                    query=query_request.query,
                    results=results
                )
        
        except Exception as e:
            logger.error(f"Error analyzing query or searching: {str(e)}")
            # Return empty results on error
            return SearchResponse(
                query=query_request.query,
                results=[]
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in search_projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 2. Get all projects endpoint
@app.get("/api/projects", response_model=ProjectList)
async def list_all_projects():
    """Get a list of all projects"""
    try:
        logger.info("Fetching all projects")
        projects = get_all_projects()
        return ProjectList(projects=projects)
    except Exception as e:
        logger.error(f"Error fetching all projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

# 3. Get project details endpoint
@app.get("/api/projects/{project_title}", response_model=ProjectDetail)
async def get_project(project_title: str):
    """Get detailed information about a specific project"""
    try:
        logger.info(f"Fetching project details for: {project_title}")
        project = get_project_by_title(project_title)
        
        if not project:
            # Create default fallback project
            project = create_default_project(project_title)
            logger.warning(f"Project not found, returning default: {project_title}")
            raise HTTPException(status_code=404, detail=f"Project not found: {project_title}")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching project details: {str(e)}")

# 4. Delete project endpoint
@app.delete("/api/projects/{project_title}")
async def delete_project(project_title: str):
    """Delete a project by title"""
    try:
        logger.info(f"Deleting project: {project_title}")
        result = delete_project_by_title(project_title)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_title}")
        
        return {"message": f"Project deleted successfully: {project_title}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")

# 5. Update project endpoint
@app.put("/api/projects/{project_title}", response_model=ProjectDetail)
async def update_project_manually(project_title: str, project: ProjectCreate):
    """Update project information manually"""
    try:
        logger.info(f"Updating project: {project_title}")
        
        # Check if project exists
        existing_project = get_project_by_title(project_title)
        if not existing_project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_title}")
        
        # Convert project title to a valid id format
        project_id = project_title.lower().replace(' ', '_').replace(',', '')
        
        # Format the new project data
        new_project_data = format_project_data(
            title_and_location=project.title_and_location,
            year_completed=project.year_completed,
            project_owner=project.project_owner,
            point_of_contact_name=project.point_of_contact_name,
            point_of_contact_telephone_number=project.point_of_contact_telephone_number,
            brief_description=project.brief_description,
            firms_from_section_c_involved_with_this_project=project.firms_from_section_c_involved_with_this_project
        )
        
        # Get existing project data from Supabase
        result = supabase.table('section_f_projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching existing project: {result.error}")
            raise HTTPException(status_code=500, detail=f"Error updating project: {result.error}")
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_title}")
        
        # Get existing project data
        existing_data = result.data[0]
        existing_project_data = existing_data.get('project_data', {})
        file_id = existing_data.get('file_id')
        
        # If existing_project_data is a string, parse it
        if isinstance(existing_project_data, str):
            try:
                existing_project_data = json.loads(existing_project_data)
            except Exception as e:
                logger.error(f"Error parsing existing project data: {e}")
                existing_project_data = {}
        
        # Merge existing data with new data
        merged_data = merge_project_data(new_project_data, existing_project_data)
        
        # Generate embedding for the project data
        project_text = json.dumps(merged_data)
        embedding = generate_embedding(project_text)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for project data")
        
        # Update the project in Supabase
        update_data = {
            "project_key": merged_data["title_and_location"],
            "file_id": file_id,
            "project_data": merged_data,
            "embedding": embedding
        }
        
        # Update the vector in Supabase
        update_result = supabase.table('section_f_projects').update(update_data).eq('id', project_id).execute()
        
        if hasattr(update_result, 'error') and update_result.error:
            logger.error(f"Error updating project: {update_result.error}")
            raise HTTPException(status_code=500, detail=f"Error updating project: {update_result.error}")
        
        logger.info(f"Successfully updated project: {project_title}")
        
        # Return the updated project
        updated_project = ProjectDetail(
            title_and_location=merged_data["title_and_location"],
            year_completed=merged_data["year_completed"],
            project_owner=merged_data["project_owner"],
            point_of_contact_name=merged_data["point_of_contact_name"],
            point_of_contact_telephone_number=merged_data["point_of_contact_telephone_number"],
            brief_description=merged_data["brief_description"],
            firms_from_section_c_involved_with_this_project=merged_data["firms_from_section_c_involved_with_this_project"],
            file_id=file_id
        )
        
        return updated_project
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")

# 6. Merge projects endpoint
@app.post("/api/merge_projects")
async def merge_projects(source_title: str, target_title: str):
    """
    Merge two projects, combining their information
    
    Args:
        source_title: The title of the source project
        target_title: The title of the target project
    """
    try:
        logger.info(f"Merging projects: {source_title} into {target_title}")
        
        # Check if both projects exist
        source_project = get_project_by_title(source_title)
        if not source_project:
            raise HTTPException(status_code=404, detail=f"Source project not found: {source_title}")
        
        target_project = get_project_by_title(target_title)
        if not target_project:
            raise HTTPException(status_code=404, detail=f"Target project not found: {target_title}")
        
        # Convert source and target project to dictionaries
        source_data = source_project.dict(exclude_unset=True)
        target_data = target_project.dict(exclude_unset=True)
        
        # Merge the data
        merged_data = merge_project_data(source_data, target_data)
        
        # Convert target title to a valid id format
        target_id = target_title.lower().replace(' ', '_').replace(',', '')
        
        # Generate embedding for the merged data
        project_text = json.dumps(merged_data)
        embedding = generate_embedding(project_text)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for merged project data")
        
        # Update the target project in Supabase
        update_data = {
            "project_key": merged_data["title_and_location"],
            "file_id": merged_data.get("file_id"),
            "project_data": merged_data,
            "embedding": embedding
        }
        
        # Update the vector in Supabase
        update_result = supabase.table('section_f_projects').update(update_data).eq('id', target_id).execute()
        
        if hasattr(update_result, 'error') and update_result.error:
            logger.error(f"Error updating target project: {update_result.error}")
            raise HTTPException(status_code=500, detail=f"Error updating target project: {update_result.error}")
        
        # Delete the source project
        delete_result = delete_project_by_title(source_title)
        
        if not delete_result:
            logger.warning(f"Failed to delete source project after merge: {source_title}")
        
        logger.info(f"Successfully merged projects: {source_title} into {target_title}")
        
        return {
            "message": f"Successfully merged projects: {source_title} into {target_title}",
            "merged_project": merged_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error merging projects: {str(e)}")

# 7. Add project via file upload endpoint
@app.post("/api/projects", response_model=ProjectDetail)
async def add_project(
    file: UploadFile = File(...),
    project_title: str = Form(None)
):
    """
    Add a new project by uploading a file
    
    Args:
        file: The PDF file to upload
        project_title: The title of the project (optional)
    """
    try:
        logger.info(f"Processing project file upload: {file.filename}")
        
        # Create a temporary file to store the uploaded content
        temp_file_path = f"/tmp/{uuid.uuid4()}.pdf"
        
        try:
            # Write the uploaded file to the temporary location
            with open(temp_file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # Derive a project title from the filename if not provided
            if not project_title:
                project_title = os.path.splitext(file.filename)[0].replace("_", " ").title()
                logger.info(f"Using derived project title: {project_title}")
            
            # Upload to Mistral for OCR processing
            pdf_url = upload_pdf_to_mistral(temp_file_path)
            logger.info(f"File uploaded to Mistral: {pdf_url}")
            
            # Extract structured data from the PDF
            structured_data = extract_structured_data_with_mistral(pdf_url)
            logger.info(f"Extracted structured data for project: {project_title}")
            
            # Generate a unique file ID (but don't upload to bucket)
            file_id = f"{uuid.uuid4()}.pdf"
            
            # Add file_id to structured data for reference only
            structured_data["file_id"] = file_id
            
            # Store in Supabase Vector Store (without actual file)
            upsert_project_in_supabase(
                project_title=structured_data.get("title_and_location", project_title),
                file_id=None,  # No file in storage
                project_data=structured_data
            )
            
            # Create and return the project detail
            project_detail = ProjectDetail(
                title_and_location=structured_data.get("title_and_location", project_title),
                year_completed=structured_data.get("year_completed", {}),
                project_owner=structured_data.get("project_owner", "Not provided"),
                point_of_contact_name=structured_data.get("point_of_contact_name", "Not provided"),
                point_of_contact_telephone_number=structured_data.get("point_of_contact_telephone_number", "Not provided"),
                brief_description=structured_data.get("brief_description", "Not provided"),
                firms_from_section_c_involved_with_this_project=structured_data.get("firms_from_section_c_involved_with_this_project", []),
                file_id=None  # No file in storage
            )
            
            return project_detail
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    except Exception as e:
        logger.error(f"Error processing project file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# 8. Add project manually endpoint
@app.post("/api/projects/manual", response_model=ProjectDetail)
async def add_project_manually(project: ProjectCreate):
    """
    Add a new project manually with provided data
    
    Args:
        project: The project data to add
    """
    try:
        logger.info(f"Adding project manually: {project.title_and_location}")
        
        # Format the project data
        project_data = format_project_data(
            title_and_location=project.title_and_location,
            year_completed=project.year_completed,
            project_owner=project.project_owner,
            point_of_contact_name=project.point_of_contact_name,
            point_of_contact_telephone_number=project.point_of_contact_telephone_number,
            brief_description=project.brief_description,
            firms_from_section_c_involved_with_this_project=project.firms_from_section_c_involved_with_this_project
        )
        
        # Convert project title to a valid id format
        project_id = project.title_and_location.lower().replace(' ', '_').replace(',', '')
        
        # Generate embedding for the project data
        project_text = json.dumps(project_data)
        embedding = generate_embedding(project_text)
        
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for project data")
        
        # Check if project already exists
        result = supabase.table('section_f_projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error checking project existence: {result.error}")
            raise HTTPException(status_code=500, detail=f"Error adding project: {result.error}")
        
        # If project exists, update it with new data
        if result.data:
            logger.info(f"Project already exists, updating: {project.title_and_location}")
            
            # Get existing data
            existing_data = result.data[0]
            existing_project_data = existing_data.get('project_data', {})
            
            # If existing_project_data is a string, parse it
            if isinstance(existing_project_data, str):
                try:
                    existing_project_data = json.loads(existing_project_data)
                except Exception as e:
                    logger.error(f"Error parsing existing project data: {e}")
                    existing_project_data = {}
            
            # Merge with existing data
            merged_data = merge_project_data(project_data, existing_project_data)
            
            # Update the project in Supabase
            update_data = {
                "project_key": merged_data["title_and_location"],
                "project_data": merged_data,
                "embedding": embedding
            }
            
            # Update the vector in Supabase
            update_result = supabase.table('section_f_projects').update(update_data).eq('id', project_id).execute()
            
            if hasattr(update_result, 'error') and update_result.error:
                logger.error(f"Error updating project: {update_result.error}")
                raise HTTPException(status_code=500, detail=f"Error updating project: {update_result.error}")
            
            logger.info(f"Successfully updated project: {project.title_and_location}")
            
            # Return the updated project
            updated_project = ProjectDetail(
                title_and_location=merged_data["title_and_location"],
                year_completed=merged_data["year_completed"],
                project_owner=merged_data["project_owner"],
                point_of_contact_name=merged_data["point_of_contact_name"],
                point_of_contact_telephone_number=merged_data["point_of_contact_telephone_number"],
                brief_description=merged_data["brief_description"],
                firms_from_section_c_involved_with_this_project=merged_data["firms_from_section_c_involved_with_this_project"],
                file_id=merged_data.get("file_id")
            )
            
            return updated_project
        
        # Otherwise, create a new project
        else:
            logger.info(f"Creating new project: {project.title_and_location}")
            
            # Insert into Supabase
            insert_data = {
                "id": project_id,
                "project_key": project.title_and_location,
                "project_data": project_data,
                "embedding": embedding
            }
            
            # Insert the vector into Supabase
            insert_result = supabase.table('section_f_projects').insert(insert_data).execute()
            
            if hasattr(insert_result, 'error') and insert_result.error:
                logger.error(f"Error inserting project: {insert_result.error}")
                raise HTTPException(status_code=500, detail=f"Error adding project: {insert_result.error}")
            
            logger.info(f"Successfully added project: {project.title_and_location}")
            
            # Return the new project
            new_project = ProjectDetail(
                title_and_location=project_data["title_and_location"],
                year_completed=project_data["year_completed"],
                project_owner=project_data["project_owner"],
                point_of_contact_name=project_data["point_of_contact_name"],
                point_of_contact_telephone_number=project_data["point_of_contact_telephone_number"],
                brief_description=project_data["brief_description"],
                firms_from_section_c_involved_with_this_project=project_data["firms_from_section_c_involved_with_this_project"],
                file_id=None
            )
            
            return new_project
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding project manually: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding project: {str(e)}")

@app.post("/api/projects_from_employee_api/{employee_name}")
async def import_projects_from_employee_api(employee_name: str):
    """
    Import projects from an employee in the employees API.
    This is a bridge between the employee API and projects API.
    
    Args:
        employee_name: The name of the employee whose projects to import
        
    Returns:
        Dict with status and list of imported projects
    """
    try:
        logger.info(f"Importing projects from employee API for: {employee_name}")
        
        # Import the employee API functions
        try:
            # Add API directory to path
            api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../API"))
            if api_dir not in sys.path:
                sys.path.append(api_dir)
            
            # Import the employee API functions
            from API.database import get_employee_by_name
            
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
                return {"status": "No projects found", "projects_imported": []}
            
            # Track imported projects
            imported_projects = []
            
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
                
                # Add to list of imported projects
                imported_projects.append({
                    "project_id": project_id,
                    "title": title_and_location
                })
            
            return {
                "status": "success",
                "projects_imported": imported_projects
            }
        
        except ImportError as e:
            logger.error(f"Error importing employee API functions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error importing employee API: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error importing projects from employee {employee_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing projects: {str(e)}")

@app.post("/api/projects_from_all_employees")
async def import_projects_from_all_employees():
    """
    Import projects from all employees in the employees API.
    This is a bridge between the employee API and projects API.
    
    Returns:
        Dict with status and summary of imported projects
    """
    try:
        logger.info("Importing projects from all employees")
        
        # Import the employee API functions
        try:
            # Add API directory to path
            api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../API"))
            if api_dir not in sys.path:
                sys.path.append(api_dir)
            
            # Import the employee API functions
            from API.database import get_all_employees
            
            # Get all employees
            employees = get_all_employees()
            
            if not employees:
                return {"status": "No employees found", "summary": {}}
            
            results = {}
            total_projects_imported = 0
            
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
                    result = await import_projects_from_employee_api(employee_name)
                    projects_imported = result.get("projects_imported", [])
                    results[employee_name] = len(projects_imported)
                    total_projects_imported += len(projects_imported)
                    
                    logger.info(f"Imported {len(projects_imported)} projects for employee {employee_name}")
                except Exception as e:
                    logger.error(f"Error processing employee {employee_name}: {str(e)}")
                    results[employee_name] = f"Error: {str(e)}"
            
            return {
                "status": "success",
                "total_projects_imported": total_projects_imported,
                "summary": results
            }
        
        except ImportError as e:
            logger.error(f"Error importing employee API functions: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error importing employee API: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error importing projects from all employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing projects: {str(e)}")

# Run the API with uvicorn if executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True) 
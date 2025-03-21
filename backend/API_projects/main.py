import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

# Configure path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models and database functions
from models import ProjectDetail, ProjectResponse, ProjectList, ProjectUpdate, ProjectCreate, QueryRequest
from database import (
    get_all_projects,
    get_project_by_id,
    update_project,
    delete_project,
    create_project,
    query_projects,
    text_search_by_project_owner
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(
    title="Project Profiles API",
    description="API for querying and managing project profiles stored in Supabase",
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
    return {"message": "Welcome to the Project Profiles API", "storage": "Supabase"}

# 1. Get all projects
@app.get("/api/projects", response_model=ProjectList)
async def list_all_projects():
    """
    Get a list of all projects
    """
    try:
        logger.info("Retrieving all projects")
        projects = get_all_projects()
        logger.info(f"Retrieved {len(projects)} projects")
        return ProjectList(projects=projects)
    
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving projects: {str(e)}")

# 2. Get specific project
@app.get("/api/projects/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """
    Get detailed information about a specific project
    """
    try:
        logger.info(f"Retrieving project details for: {project_id}")
        project = get_project_by_id(project_id)
        
        if not project:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        logger.info(f"Successfully retrieved project details for: {project_id}")
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving project details: {str(e)}")

# 3. Create new project
@app.post("/api/projects", response_model=ProjectDetail)
async def add_project(project: ProjectCreate):
    """
    Create a new project
    """
    try:
        logger.info(f"Creating new project: {project.title_and_location}")
        new_project = create_project(project)
        
        if not new_project:
            logger.error(f"Failed to create project: {project.title_and_location}")
            raise HTTPException(status_code=500, detail="Failed to create project")
        
        logger.info(f"Successfully created project with ID: {new_project.id}")
        return new_project
    
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")

# 4. Update project
@app.put("/api/projects/{project_id}", response_model=ProjectDetail)
async def update_project_details(project_id: str, project_update: ProjectUpdate):
    """
    Update an existing project
    """
    try:
        logger.info(f"Updating project: {project_id}")
        updated_project = update_project(project_id, project_update)
        
        if not updated_project:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        logger.info(f"Successfully updated project: {project_id}")
        return updated_project
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")

# 5. Delete project
@app.delete("/api/projects/{project_id}")
async def remove_project(project_id: str):
    """
    Delete a project
    """
    try:
        logger.info(f"Deleting project: {project_id}")
        success = delete_project(project_id)
        
        if not success:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        logger.info(f"Successfully deleted project: {project_id}")
        return {"message": f"Project '{project_id}' successfully deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")

# 6. Query projects
@app.post("/api/projects/query", response_model=ProjectList)
async def search_projects(query_request: QueryRequest):
    """
    Search for projects based on a natural language query
    """
    try:
        logger.info(f"API Endpoint: Searching for projects with query: {query_request.query}")
        
        # Add some debug information about the query
        logger.info(f"Query parameters: text='{query_request.query}', limit={query_request.limit}")
        
        # Query for projects
        projects = query_projects(query_request.query, query_request.limit)
        
        # Log detailed information about the results
        logger.info(f"Found {len(projects)} projects matching the query")
        if projects:
            for i, project in enumerate(projects):
                logger.info(f"  Result {i+1}: id={project.id}, title={project.title_and_location}, owner={project.project_owner}, score={project.score}")
        else:
            logger.warning(f"No projects found for query: '{query_request.query}'")
        
        return ProjectList(projects=projects)
    
    except Exception as e:
        logger.error(f"Error querying projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error querying projects: {str(e)}")

# 7. Search projects by owner
@app.get("/api/projects/owner/{owner_text}", response_model=ProjectList)
async def search_projects_by_owner(owner_text: str, limit: int = 10):
    """
    Search for projects by owner name
    """
    try:
        logger.info(f"Searching for projects with owner containing: '{owner_text}'")
        
        # Use dedicated function for text search by owner
        projects = text_search_by_project_owner(owner_text)
        
        # Limit results
        limited_projects = projects[:limit]
        
        logger.info(f"Found {len(limited_projects)} projects with owner containing '{owner_text}'")
        if limited_projects:
            for i, project in enumerate(limited_projects):
                logger.info(f"  Result {i+1}: id={project.id}, title={project.title_and_location}, owner={project.project_owner}")
        else:
            logger.warning(f"No projects found with owner containing '{owner_text}'")
        
        return ProjectList(projects=limited_projects)
    
    except Exception as e:
        logger.error(f"Error searching projects by owner: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching projects by owner: {str(e)}")

# Run the API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
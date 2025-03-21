#!/usr/bin/env python
"""
Simple API implementation for project retrieval
This script starts a FastAPI server on port 8002 to demonstrate project retrieval
"""
import os
import json
import logging
import sys
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from supabase import create_client
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("simple_api")

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
supabase = create_client(supabase_url, supabase_key)

# Define basic models
class Firm(BaseModel):
    firm_name: str
    firm_location: str
    role: str

class YearCompleted(BaseModel):
    professional_services: Optional[str] = None
    construction: Optional[str] = None

class ProjectDetail(BaseModel):
    id: str
    title_and_location: str
    project_owner: str
    point_of_contact_name: str
    point_of_contact: str
    brief_description: str
    year_completed: YearCompleted
    firms_from_section_c: List[Firm]

class ProjectResponse(BaseModel):
    id: str
    title_and_location: str
    project_owner: str
    score: float = 1.0

class ProjectList(BaseModel):
    projects: List[ProjectResponse]

# Create FastAPI app
app = FastAPI(
    title="Simple Project API",
    description="Minimal API for testing project retrieval",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def simple_get_project_by_id(project_id: str) -> Optional[ProjectDetail]:
    """
    A direct and simple version of get_project_by_id
    """
    try:
        logger.info(f"Retrieving project with ID: {project_id}")
        
        # Query Supabase directly
        result = supabase.table('projects').select('id, title, project_data').eq('id', project_id).execute()
        
        if not result.data or len(result.data) == 0:
            logger.warning(f"Project with ID '{project_id}' not found")
            return None
        
        # Get project data
        project_item = result.data[0]
        project_id = project_item.get('id', '')
        title = project_item.get('title', '')
        project_data = project_item.get('project_data', {})
        
        # Create basic project structure
        project_dict = {
            "id": project_id,
            "title_and_location": title,
            "project_owner": "Unknown",
            "point_of_contact_name": "Unknown",
            "point_of_contact": "Unknown",
            "brief_description": "No description available",
            "year_completed": {
                "professional_services": None,
                "construction": None
            },
            "firms_from_section_c": []
        }
        
        # Update with project_data values if available
        if project_data and isinstance(project_data, dict):
            # Handle title_and_location
            if 'title_and_location' in project_data:
                if isinstance(project_data['title_and_location'], dict):
                    title_dict = project_data['title_and_location']
                    title_part = title_dict.get('title', '')
                    location_part = title_dict.get('location', '')
                    project_dict['title_and_location'] = f"{title_part}, {location_part}" if location_part else title_part
                else:
                    project_dict['title_and_location'] = str(project_data['title_and_location'])
            
            # Handle simple string fields
            for field in ['project_owner', 'point_of_contact_name', 'brief_description']:
                if field in project_data:
                    project_dict[field] = str(project_data[field])
            
            # Handle point_of_contact
            if 'point_of_contact' in project_data:
                if isinstance(project_data['point_of_contact'], dict):
                    contact_dict = project_data['point_of_contact']
                    contact_parts = []
                    if 'email' in contact_dict:
                        contact_parts.append(f"Email: {contact_dict['email']}")
                    if 'phone' in contact_dict:
                        contact_parts.append(f"Phone: {contact_dict['phone']}")
                    if contact_parts:
                        project_dict['point_of_contact'] = ", ".join(contact_parts)
                else:
                    project_dict['point_of_contact'] = str(project_data['point_of_contact'])
                    
            # Handle year_completed
            if 'year_completed' in project_data and isinstance(project_data['year_completed'], dict):
                year_data = project_data['year_completed']
                project_dict['year_completed'] = {
                    'professional_services': year_data.get('professional_services'),
                    'construction': year_data.get('construction')
                }
            
            # Handle firms_from_section_c
            if 'firms_from_section_c' in project_data and isinstance(project_data['firms_from_section_c'], list):
                firms = []
                for firm in project_data['firms_from_section_c']:
                    if isinstance(firm, dict):
                        firms.append({
                            "firm_name": firm.get('firm_name', "Unknown"),
                            "firm_location": firm.get('firm_location', "Unknown"),
                            "role": firm.get('role', "Unknown")
                        })
                project_dict['firms_from_section_c'] = firms
        
        # Create and return the ProjectDetail object
        return ProjectDetail(**project_dict)
    
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        logger.exception(e)
        return None

def simple_get_all_projects() -> List[ProjectResponse]:
    """
    A direct and simple version of get_all_projects
    """
    try:
        logger.info("Retrieving all projects")
        
        # Query Supabase directly
        result = supabase.table('projects').select('id, title, project_data').execute()
        
        if not result.data:
            logger.warning("No projects found")
            return []
        
        projects = []
        
        for item in result.data:
            try:
                project_id = item.get('id', '')
                title = item.get('title', '')
                project_data = item.get('project_data', {})
                
                # Extract title_and_location and project_owner
                title_and_location = title
                project_owner = "Unknown"
                
                if project_data and isinstance(project_data, dict):
                    # Handle title_and_location
                    if 'title_and_location' in project_data:
                        if isinstance(project_data['title_and_location'], dict):
                            title_dict = project_data['title_and_location']
                            title_part = title_dict.get('title', '')
                            location_part = title_dict.get('location', '')
                            title_and_location = f"{title_part}, {location_part}" if location_part else title_part
                        else:
                            title_and_location = str(project_data['title_and_location'])
                    
                    # Handle project_owner
                    if 'project_owner' in project_data:
                        project_owner = str(project_data['project_owner'])
                
                # Create and add the ProjectResponse
                projects.append(
                    ProjectResponse(
                        id=project_id,
                        title_and_location=title_and_location,
                        project_owner=project_owner,
                        score=1.0
                    )
                )
                
            except Exception as e:
                logger.error(f"Error processing project: {str(e)}")
                logger.exception(e)
                continue
        
        return projects
    
    except Exception as e:
        logger.error(f"Error retrieving all projects: {str(e)}")
        logger.exception(e)
        return []

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Simple Project API is running"}

@app.get("/api/projects", response_model=ProjectList)
async def list_projects():
    """
    Get a list of all projects
    """
    try:
        logger.info("API: Retrieving all projects")
        projects = simple_get_all_projects()
        logger.info(f"Found {len(projects)} projects")
        return ProjectList(projects=projects)
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """
    Get details for a specific project
    """
    try:
        logger.info(f"API: Retrieving project with ID: {project_id}")
        project = simple_get_project_by_id(project_id)
        
        if not project:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        logger.info(f"Successfully retrieved project: {project.title_and_location}")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project: {str(e)}")
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))

# Run the API server
if __name__ == "__main__":
    logger.info("Starting Simple Project API on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002) 
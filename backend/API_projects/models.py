from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# Request Models
class QueryRequest(BaseModel):
    """Model for search query requests"""
    query: str = Field(..., description="The search query to find relevant projects")

class ProjectCreate(BaseModel):
    """Model for creating a new project"""
    title_and_location: str = Field(..., description="Project title and location")
    year_completed: Optional[Dict[str, Any]] = Field(None, description="Year professional services and construction were completed")
    project_owner: Optional[str] = Field(None, description="Name of the project owner")
    point_of_contact_name: Optional[str] = Field(None, description="Full name and title of the point of contact")
    point_of_contact_telephone_number: Optional[str] = Field(None, description="Phone number of the point of contact")
    brief_description: Optional[str] = Field(None, description="Brief description of the project")
    firms_from_section_c_involved_with_this_project: Optional[List[Dict[str, Any]]] = Field(None, description="Firms involved with the project")

# Response Models
class ProjectResponse(BaseModel):
    """Basic project information for search results"""
    title_and_location: str
    project_owner: str
    score: float
    year_completed: Any = None
    brief_description: str = None

class ProjectDetail(BaseModel):
    """Detailed project information"""
    title_and_location: str
    year_completed: Optional[Union[Dict[str, Any], Any]] = None
    project_owner: Optional[str] = None
    point_of_contact_name: Optional[str] = None
    point_of_contact_telephone_number: Optional[str] = None
    brief_description: Optional[str] = None
    firms_from_section_c_involved_with_this_project: Optional[Union[List[Dict[str, Any]], Any]] = None
    file_id: Optional[Union[List[str], str, Any]] = None
    
    class Config:
        """Configuration for the model"""
        # Allow arbitrary types for fields
        arbitrary_types_allowed = True
        # Populate models with the name of fields from aliases
        orm_mode = True
        # Prevent validation errors for empty fields
        validate_assignment = False
        # Make fields optional
        extra = "allow"

class ProjectList(BaseModel):
    """List of projects"""
    projects: List[ProjectResponse]

class SearchResponse(BaseModel):
    """Response model for search queries"""
    query: str
    results: List[ProjectResponse] 
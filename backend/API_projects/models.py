from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# Year completed model
class YearCompleted(BaseModel):
    professional_services: Optional[Union[int, str]] = None
    construction: Optional[Union[int, str]] = None

# Firm model
class Firm(BaseModel):
    firm_name: str = "Unknown"
    firm_location: str = "Unknown"
    role: str = "Unknown"

# Title and Location model
class TitleAndLocation(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None

# Point of Contact model
class PointOfContact(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None

# Base project model with common fields
class ProjectBase(BaseModel):
    title: Optional[str] = ""

# Model for creating a new project
class ProjectCreate(ProjectBase):
    title_and_location: Optional[TitleAndLocation] = None
    project_owner: Optional[str] = None
    brief_description: Optional[str] = None
    point_of_contact: Optional[PointOfContact] = None
    year_completed: Optional[YearCompleted] = None
    firms_from_section_c: Optional[List[Firm]] = None

# Model for updating an existing project
class ProjectUpdate(ProjectBase):
    title_and_location: Optional[TitleAndLocation] = None
    project_owner: Optional[str] = None
    brief_description: Optional[str] = None
    point_of_contact: Optional[PointOfContact] = None
    year_completed: Optional[YearCompleted] = None
    firms_from_section_c: Optional[List[Firm]] = None

# Model for detailed project information
class ProjectDetail(BaseModel):
    id: str
    title: str = ""
    title_and_location: Optional[TitleAndLocation] = None
    project_owner: str = ""
    brief_description: str = ""
    point_of_contact: Optional[PointOfContact] = None
    year_completed: Optional[YearCompleted] = None
    firms_from_section_c: List[Firm] = []

# Model for project search results
class ProjectResponse(BaseModel):
    id: str
    title: str
    project_owner: str = ""
    score: float = 1.0

# Model for query request
class QueryRequest(BaseModel):
    query: str
    limit: int = 10

# Model for list of projects
class ProjectList(BaseModel):
    projects: List[ProjectResponse] 
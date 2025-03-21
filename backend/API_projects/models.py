from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

# Year completed model
class YearCompleted(BaseModel):
    professional_services: Optional[Union[int, str]] = None
    construction: Optional[Union[int, str]] = None

# Firm model
class Firm(BaseModel):
    firm_name: str
    firm_location: str
    role: str

# Base project model with common fields
class ProjectBase(BaseModel):
    title_and_location: str
    year_completed: YearCompleted
    project_owner: str
    point_of_contact_name: str
    point_of_contact: str
    brief_description: str
    firms_from_section_c: List[Firm]

# Model for creating a new project
class ProjectCreate(ProjectBase):
    pass

# Model for updating an existing project
class ProjectUpdate(BaseModel):
    title_and_location: Optional[str] = None
    year_completed: Optional[YearCompleted] = None
    project_owner: Optional[str] = None
    point_of_contact_name: Optional[str] = None
    point_of_contact: Optional[str] = None
    brief_description: Optional[str] = None
    firms_from_section_c: Optional[List[Firm]] = None

# Model for detailed project information
class ProjectDetail(ProjectBase):
    id: str

# Model for project search results
class ProjectResponse(BaseModel):
    id: str
    title_and_location: str
    project_owner: str
    score: float = 1.0

# Model for query request
class QueryRequest(BaseModel):
    query: str
    limit: int = 10

# Model for list of projects
class ProjectList(BaseModel):
    projects: List[ProjectResponse] 
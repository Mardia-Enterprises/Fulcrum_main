from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# Request Models
class QueryRequest(BaseModel):
    """Model for search query requests"""
    query: str = Field(..., description="The search query to find relevant employees")

class EmployeeCreate(BaseModel):
    """Model for creating a new employee"""
    name: str = Field(..., description="Employee's full name")
    role: Optional[str] = Field(None, description="Employee's role in contract")
    years_experience: Optional[Dict[str, Any]] = Field(None, description="Years of experience (total and with current firm)")
    firm: Optional[Dict[str, Any]] = Field(None, description="Firm name and location")
    education: Optional[Union[List[Dict[str, Any]], str]] = Field(None, description="Education details")
    professional_registrations: Optional[List[Dict[str, Any]]] = Field(None, description="Professional registrations")
    other_qualifications: Optional[str] = Field(None, description="Other professional qualifications")
    relevant_projects: Optional[List[Dict[str, Any]]] = Field(None, description="Relevant projects")

# Response Models
class EmployeeResponse(BaseModel):
    """Basic employee information for search results"""
    name: str
    role: str
    score: float
    education: Any
    years_experience: Any = None
    relevant_projects: List[Any]
    matching_project_info: Optional[Dict[str, Any]] = None

class EmployeeDetail(BaseModel):
    """Detailed employee information"""
    name: str
    role: Optional[Union[str, List[str]]] = None
    years_experience: Optional[Union[Dict[str, Any], str, Any]] = None
    firm: Optional[Union[Dict[str, Any], str, Any]] = None
    education: Optional[Union[List[Dict[str, Any]], List[str], str, Any]] = None
    professional_registrations: Optional[Union[List[Dict[str, Any]], List[str], str, Any]] = None
    other_qualifications: Optional[Union[str, Any]] = None
    relevant_projects: Optional[Union[List[Dict[str, Any]], List[str], Any]] = None
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

class EmployeeList(BaseModel):
    """List of employees"""
    employees: List[EmployeeResponse]

class SearchResponse(BaseModel):
    """Response model for search queries"""
    query: str
    results: List[EmployeeResponse] 
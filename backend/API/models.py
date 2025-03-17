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
    relevant_projects: List[Any]

class EmployeeDetail(BaseModel):
    """Detailed employee information"""
    name: str
    role: Optional[str] = None
    years_experience: Optional[Dict[str, Any]] = None
    firm: Optional[Dict[str, Any]] = None
    education: Optional[Any] = None
    professional_registrations: Optional[List[Dict[str, Any]]] = None
    other_qualifications: Optional[str] = None
    relevant_projects: Optional[List[Dict[str, Any]]] = None
    file_id: Optional[List[str]] = None

class EmployeeList(BaseModel):
    """List of employees"""
    employees: List[EmployeeResponse]

class SearchResponse(BaseModel):
    """Response model for search queries"""
    query: str
    results: List[EmployeeResponse] 
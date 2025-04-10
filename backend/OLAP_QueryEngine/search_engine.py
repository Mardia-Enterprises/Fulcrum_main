import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import argparse

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("search_engine")

# Load environment variables
load_dotenv()

# Configure Supabase client
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
if not supabase_url or not supabase_key:
    logger.error("Supabase credentials not found in .env file")
    logger.error("Please set SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY in your .env file")
    supabase = None
else:
    try:
        # Create the Supabase client
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        supabase = None

# Configure OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OpenAI API key not found in .env file")
    logger.error("Please set OPENAI_API_KEY in your .env file")
    openai_client = None
else:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        openai_embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        logger.info(f"Successfully initialized OpenAI client with model {openai_model}")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None


def verify_environment():
    """Verify that all required components are available"""
    if not supabase:
        logger.error("Supabase client is not configured properly")
        return False
    
    if not openai_client:
        logger.error("OpenAI client is not configured properly")
        return False
    
    logger.info("Environment verification passed")
    return True


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text using OpenAI's embeddings API"""
    if not openai_client:
        logger.error("OpenAI client not available for embeddings")
        return []
    
    try:
        response = openai_client.embeddings.create(
            model=openai_embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return []


def search_teams(query: str) -> List[Dict[str, Any]]:
    """Search for employees based on name or role"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        # First try direct text search - more permissive search
        # Split the query into individual terms for better matching
        query_terms = query.split()
        
        # If it's a person's name, look for parts of the name
        text_search = supabase.table('employee').select('*').or_(
            f"name.ilike.%{query}%,role.ilike.%{query}%"
        ).execute()
        
        results = text_search.data

        # Search for individual terms if no direct match found
        if len(results) == 0 and len(query_terms) > 1:
            for term in query_terms:
                if len(term) > 2:  # Only search for meaningful terms
                    partial_search = supabase.table('employee').select('*').or_(
                        f"name.ilike.%{term}%,role.ilike.%{term}%"
                    ).execute()
                    results.extend(partial_search.data)
            
            # Remove duplicates
            seen_ids = set()
            unique_results = []
            for item in results:
                if item['id'] not in seen_ids:
                    seen_ids.add(item['id'])
                    unique_results.append(item)
            results = unique_results
        
        # If no results or few results, try semantic search with embeddings
        # Only if match_employees function is available
        if len(results) < 3:
            try:
                query_embedding = generate_embedding(query)
                if query_embedding:
                    # Search using vector similarity
                    vector_search = supabase.rpc(
                        "match_employees", 
                        {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": 10}
                    ).execute()
                    
                    # Merge results, prioritizing text search matches
                    if vector_search.data:
                        # Create a set of IDs we already have
                        existing_ids = {employee['id'] for employee in results}
                        # Add vector search results that don't overlap
                        for employee in vector_search.data:
                            if employee['id'] not in existing_ids:
                                results.append(employee)
            except Exception as e:
                logger.warning(f"Vector search for employees not available: {e}")
                # Continue with just the text search results
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching employees: {e}")
        return []


def search_projects(query: str) -> List[Dict[str, Any]]:
    """Search for projects based on name or location"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        # Direct text search - more permissive search
        # Split the query into individual terms for better matching
        query_terms = query.split()
        
        text_search = supabase.table('projects').select('*').or_(
            f"name.ilike.%{query}%,location.ilike.%{query}%"
        ).execute()
        
        results = text_search.data

        # Search for individual terms if no direct match found
        if len(results) == 0 and len(query_terms) > 1:
            for term in query_terms:
                if len(term) > 2:  # Only search for meaningful terms
                    partial_search = supabase.table('projects').select('*').or_(
                        f"name.ilike.%{term}%,location.ilike.%{term}%"
                    ).execute()
                    results.extend(partial_search.data)
            
            # Remove duplicates
            seen_ids = set()
            unique_results = []
            for item in results:
                if item['id'] not in seen_ids:
                    seen_ids.add(item['id'])
                    unique_results.append(item)
            results = unique_results
        
        # Add semantic search here if needed in the future
        # For now, projects don't have embeddings in the schema
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        return []


def get_team_projects(team_id: str) -> List[Dict[str, Any]]:
    """Get all projects for a specific employee"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        # Query employee_projects to get project IDs and text_id
        employee_projects = supabase.table('employee_projects').select('project_id, text_id, role').eq('employee_id', team_id).execute()
        
        if not employee_projects.data:
            return []
        
        # Collect project IDs
        project_ids = [ep['project_id'] for ep in employee_projects.data]
        
        # Get project details
        if project_ids:
            projects_data = supabase.table('projects').select('*').in_('id', project_ids).execute()
            
            # Add text_id and role to each project
            projects = projects_data.data
            text_id_by_project = {ep['project_id']: ep.get('text_id') for ep in employee_projects.data}
            role_by_project = {ep['project_id']: ep.get('role') for ep in employee_projects.data}
            
            for project in projects:
                project['text_id'] = text_id_by_project.get(project['id'])
                project['employee_role'] = role_by_project.get(project['id'])
            
            return projects
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting employee projects: {e}")
        return []


def get_project_teams(project_id: str) -> List[Dict[str, Any]]:
    """Get all employees for a specific project"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        # Query employee_projects to get employee IDs
        project_employees = supabase.table('employee_projects').select('employee_id, text_id, role').eq('project_id', project_id).execute()
        
        if not project_employees.data:
            return []
        
        # Collect employee IDs
        employee_ids = [pe['employee_id'] for pe in project_employees.data]
        
        # Get employee details
        if employee_ids:
            employees_data = supabase.table('employee').select('*').in_('id', employee_ids).execute()
            
            # Add text_id and role to each employee record
            employees = employees_data.data
            text_id_by_employee = {pe['employee_id']: pe.get('text_id') for pe in project_employees.data}
            role_by_employee = {pe['employee_id']: pe.get('role') for pe in project_employees.data}
            
            for employee in employees:
                employee['text_id'] = text_id_by_employee.get(employee['id'])
                employee['project_role'] = role_by_employee.get(employee['id'])
            
            return employees
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting project employees: {e}")
        return []


def get_document_text(document_id: str) -> Dict[str, Any]:
    """Get document details and text from sharded_documents"""
    if not supabase:
        logger.error("Supabase client not available")
        return {}
    
    try:
        # Get document details
        document = supabase.table('documents').select('*').eq('id', document_id).execute()
        
        if not document.data:
            return {}
        
        # Get sharded document text
        shards = supabase.table('sharded_documents').select('text_id, text').eq('document_id', document_id).execute()
        
        result = document.data[0]
        result['shards'] = [{'text_id': shard['text_id'], 'text': shard['text']} for shard in shards.data] if shards.data else []
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting document text: {e}")
        return {}


def get_document_info_by_text_id(text_id: str) -> Dict[str, Any]:
    """Get document info for a text shard by its text_id"""
    if not supabase:
        logger.error("Supabase client not available")
        return {}
    
    try:
        # First get the document_id from the shard
        shard = supabase.table('sharded_documents').select('document_id').eq('text_id', text_id).execute()
        
        if not shard.data:
            return {}
        
        document_id = shard.data[0]['document_id']
        
        # Then get the document info
        document = supabase.table('documents').select('*').eq('id', document_id).execute()
        
        if not document.data:
            return {}
        
        return document.data[0]
        
    except Exception as e:
        logger.error(f"Error getting document info for text_id: {e}")
        return {}


def get_text_from_ids(text_ids: List[str]) -> List[Dict[str, Any]]:
    """Get text from sharded_documents for a list of text IDs"""
    if not supabase or not text_ids:
        return []
    
    try:
        # Remove duplicates to avoid redundant queries
        unique_text_ids = list(set(text_ids))
        
        # Get text from sharded_documents - directly query by text_ids
        texts = supabase.table('sharded_documents').select('text_id, text, document_id').in_('text_id', unique_text_ids).execute()
        
        if not texts.data:
            return []
        
        # For each text chunk, add document link information
        results = []
        for text in texts.data:
            text_info = {
                'text_id': text['text_id'],
                'text': text['text'],
                'document_id': text['document_id'],
                'document_link': get_document_link(text['document_id'])
            }
            results.append(text_info)
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting text from IDs: {e}")
        return []


def get_relevant_text_for_employee(employee_id: str) -> List[Dict[str, Any]]:
    """Get relevant text chunks for a specific employee"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        text_ids = []
        
        # Get text_ids from employee_documents
        employee_docs = supabase.table('employee_documents').select('text_id').eq('employee_id', employee_id).execute()
        if employee_docs.data:
            text_ids.extend([doc['text_id'] for doc in employee_docs.data if 'text_id' in doc])
        
        # Get text_ids from employee_projects
        employee_projects = supabase.table('employee_projects').select('text_id').eq('employee_id', employee_id).execute()
        if employee_projects.data:
            text_ids.extend([proj['text_id'] for proj in employee_projects.data if 'text_id' in proj])
        
        # If no text_ids found, return empty list
        if not text_ids:
            return []
        
        # Get the actual text content for these text_ids
        return get_text_from_ids(text_ids)
        
    except Exception as e:
        logger.error(f"Error getting relevant text for employee: {e}")
        return []


def get_relevant_text_for_project(project_id: str) -> List[Dict[str, Any]]:
    """Get relevant text chunks for a specific project"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        text_ids = []
        
        # Get text_ids from project_documents
        project_docs = supabase.table('project_documents').select('text_id').eq('project_id', project_id).execute()
        if project_docs.data:
            text_ids.extend([doc['text_id'] for doc in project_docs.data if 'text_id' in doc])
        
        # Get text_ids from employee_projects related to this project
        employee_projects = supabase.table('employee_projects').select('text_id').eq('project_id', project_id).execute()
        if employee_projects.data:
            text_ids.extend([proj['text_id'] for proj in employee_projects.data if 'text_id' in proj])
        
        # If no text_ids found, return empty list
        if not text_ids:
            return []
        
        # Get the actual text content for these text_ids
        return get_text_from_ids(text_ids)
        
    except Exception as e:
        logger.error(f"Error getting relevant text for project: {e}")
        return []


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    if not supabase:
        return False
    
    try:
        # Use a simple query to check if the table exists
        query = f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}');"
        result = supabase.rpc("select_one", {"query_text": query}).execute()
        
        if result.data and result.data[0]:
            return result.data[0]
        return False
    except Exception as e:
        logger.warning(f"Error checking if table {table_name} exists: {e}")
        # Use a fallback method - try to select one row
        try:
            result = supabase.table(table_name).select('*').limit(1).execute()
            # If we get here, the table exists
            return True
        except Exception:
            # If we get an error, the table doesn't exist
            return False


def search_semantically(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for semantically similar content using embeddings"""
    if not supabase:
        logger.error("Supabase client not available")
        return []
    
    try:
        query_embedding = generate_embedding(query)
        if not query_embedding:
            return []
        
        try:
            # Search using vector similarity in sharded_documents
            # This directly searches text chunks, not entire documents
            semantic_results = supabase.rpc(
                "match_documents", 
                {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": limit}
            ).execute()
            
            # Add additional info to each text chunk
            results = []
            for text in semantic_results.data:
                text["document_link"] = get_document_link(text.get("document_id", ""))
                results.append(text)
            
            return results
        except Exception as e:
            logger.warning(f"Vector search not available: {e}")
            
            # Fallback to direct text search in sharded documents with improved search logic
            # Split query into meaningful terms
            query_terms = set(term.lower() for term in query.split() if len(term) > 2)
            
            # First get a sample of sharded documents to search
            # Limit to 100 to avoid searching the entire database
            text_search = supabase.table('sharded_documents').select('text_id, document_id, text').limit(100).execute()
            
            results = []
            
            for doc in text_search.data:
                # Check for exact phrases
                doc_text_lower = doc['text'].lower()
                if query.lower() in doc_text_lower:
                    doc['similarity'] = 0.9  # High score for exact phrase match
                    doc["document_link"] = get_document_link(doc.get("document_id", ""))
                    results.append(doc)
                else:
                    # Check for term matches
                    doc_terms = set(doc_text_lower.split())
                    common_terms = len(query_terms.intersection(doc_terms))
                    if common_terms > 0:
                        doc['similarity'] = common_terms / len(query_terms)
                        doc["document_link"] = get_document_link(doc.get("document_id", ""))
                        results.append(doc)
            
            # Sort by our basic similarity score
            results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            return results[:limit]
            
    except Exception as e:
        logger.error(f"Error searching semantically: {e}")
        return []


def analyze_query(query: str) -> Dict[str, Any]:
    """Analyze the query to determine what kind of information is being requested"""
    if not openai_client:
        logger.error("OpenAI client not available")
        return {"type": "unknown"}
    
    try:
        system_prompt = """
        Analyze the user's query to determine what kind of information they are looking for.
        Categorize the query into one of the following types:
        1. team_info - Looking for information about a specific team or person
        2. project_info - Looking for information about a specific project
        3. team_projects - Looking for projects associated with a specific team/person
        4. project_teams - Looking for teams/people associated with a specific project
        5. general - General query about teams or projects
        
        Also extract any specific names, entities, or key terms mentioned in the query.
        
        Return the result as a JSON object with the following fields:
        {
            "type": "team_info|project_info|team_projects|project_teams|general",
            "entities": ["entity1", "entity2"],
            "key_terms": ["term1", "term2"]
        }
        """
        
        try:
            response = openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                timeout=10  # Add a timeout
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            # Handle rate limit or timeout errors by doing a simple classification
            logger.error(f"Error analyzing query: {e}")
            
            # Fallback classification logic
            query_lower = query.lower()
            
            # Simple check for query type
            if "who is" in query_lower or "about person" in query_lower:
                return {"type": "team_info", "entities": [query], "key_terms": []}
            elif "project" in query_lower and "working on" in query_lower:
                return {"type": "team_projects", "entities": [q for q in query.split() if len(q) > 3], "key_terms": ["projects", "working on"]}
            elif "what is" in query_lower and "project" in query_lower:
                return {"type": "project_info", "entities": [query], "key_terms": ["project"]}
            else:
                return {"type": "general", "entities": [], "key_terms": [query]}
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        return {"type": "unknown", "entities": [], "key_terms": []}


def generate_response(search_results: Dict[str, Any], query: str) -> str:
    """Generate a natural language response to the query using the search results"""
    if not openai_client:
        return "OpenAI client not available for generating response"
    
    try:
        # Create a prompt with the search results
        results_json = json.dumps(search_results, indent=2)
        
        system_prompt = f"""
        You are a helpful assistant that provides information about employees and projects.
        Use the provided search results to answer the user's query.
        
        Do not make up any information that is not in the search results.
        If the search results do not contain relevant information, simply state that you don't have
        enough information to answer the query.
        
        Important: The search engine focuses on specific text chunks, not entire documents.
        When providing information, always use the text chunks and their source.
        
        When discussing employees and their related projects, be sure to mention their roles
        (both their general role and specific project roles if available) and include all relevant
        relationships found in the search results.
        
        For domain-specific queries (like "Find all employees who work on airport projects" or
        "Find all hydraulic engineers"), focus on the relevant text chunks and the employee roles.
        
        Your response should be detailed yet concise, focusing on directly answering the query with the
        information available. Include direct quotes from text chunks when appropriate.
        
        The search results include:
        - Employees: Detailed Information about employees
        - Projects: Detailed Information about projects
        - Employee Projects: Projects associated with specific employees
        - Project Employees: Employees associated with specific projects
        - Roles: Information about Employees having a specific Role
        - Documents: Relevant text chunks with their sources (specific sharded text chunks)
        - Semantic Results: Additional semantically relevant text chunks
        
        Search results: {results_json}
        """
        
        try:
            response = openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                timeout=10  # Add a timeout
            )
            
            return response.choices[0].message.content
        except Exception as e:
            # Handle rate limit or timeout errors by returning a simple response
            logger.error(f"Error generating response: {e}")
            
            # Get query type from search results
            query_type = search_results.get("query_type", "unknown")
            
            # Fallback response generation - focus on employee-project relationships
            if query_type == "team_projects" and search_results.get("employee_projects"):
                # Generate response for employee projects
                employee_projects_info = []
                text_chunks = []
                
                for ep in search_results.get("employee_projects", []):
                    employee_name = ep.get("employee_name", "Unknown employee")
                    employee_role = ep.get("employee_role", "")
                    projects = ep.get("projects", [])
                    
                    project_details = []
                    for project in projects:
                        project_name = project.get("name", "Unknown project")
                        project_location = project.get("location", "Unknown location")
                        employee_project_role = project.get("employee_role", "Contributor")
                        
                        project_info = f"- {project_name} ({project_location})"
                        if employee_project_role:
                            project_info += f" - Role: {employee_project_role}"
                        
                        project_details.append(project_info)
                    
                    # Create employee project info with role
                    emp_info = f"{employee_name}"
                    if employee_role:
                        emp_info += f" ({employee_role})"
                    emp_info += " is working on:"
                    
                    if project_details:
                        emp_info += "\n" + "\n".join(project_details)
                    else:
                        emp_info += " No project details found."
                    
                    employee_projects_info.append(emp_info)
                
                # Include relevant text chunks
                for doc in search_results.get("documents", []):
                    if "text" in doc:
                        text_chunks.append({
                            "text": doc["text"],
                            "text_id": doc.get("text_id", "Unknown"),
                            "document_link": doc.get("document_link", "Not available")
                        })
                
                if employee_projects_info:
                    response = "\n\n".join(employee_projects_info)
                else:
                    response = "No information found about projects for the specified employee(s)."
                
                # Add text chunks section if available
                if text_chunks:
                    response += "\n\nRELEVANT TEXT CHUNKS:\n"
                    for i, chunk in enumerate(text_chunks[:3], 1):  # Limit to top 3 chunks
                        response += f"\n{i}. Text ID: {chunk['text_id']}\n"
                        response += f"Source: {chunk['document_link']}\n"
                        response += f"Content: {chunk['text'][:200]}...\n"  # Show first 200 chars
                
                return response
                
            elif query_type == "project_teams" and search_results.get("project_employees"):
                # Generate response for project employees
                project_employees_info = []
                text_chunks = []
                
                for pe in search_results.get("project_employees", []):
                    project_name = pe.get("project_name", "Unknown project")
                    project_location = pe.get("project_location", "")
                    employees = pe.get("employees", [])
                    
                    employee_details = []
                    for employee in employees:
                        employee_name = employee.get("name", "Unknown employee")
                        employee_role = employee.get("role", "")
                        project_role = employee.get("project_role", "")
                        
                        employee_info = f"- {employee_name}"
                        if project_role:
                            employee_info += f" - Project Role: {project_role}"
                        elif employee_role:
                            employee_info += f" - Role: {employee_role}"
                            
                        employee_details.append(employee_info)
                    
                    # Create project info
                    proj_info = f"{project_name}"
                    if project_location:
                        proj_info += f" ({project_location})"
                    proj_info += " has the following team members:"
                    
                    if employee_details:
                        proj_info += "\n" + "\n".join(employee_details)
                    else:
                        proj_info += " No team members found."
                    
                    project_employees_info.append(proj_info)
                
                # Include relevant text chunks
                for doc in search_results.get("documents", []):
                    if "text" in doc:
                        text_chunks.append({
                            "text": doc["text"],
                            "text_id": doc.get("text_id", "Unknown"),
                            "document_link": doc.get("document_link", "Not available")
                        })
                
                if project_employees_info:
                    response = "\n\n".join(project_employees_info)
                else:
                    response = "No information found about team members for the specified project(s)."
                
                # Add text chunks section if available
                if text_chunks:
                    response += "\n\nRELEVANT TEXT CHUNKS:\n"
                    for i, chunk in enumerate(text_chunks[:3], 1):  # Limit to top 3 chunks
                        response += f"\n{i}. Text ID: {chunk['text_id']}\n"
                        response += f"Source: {chunk['document_link']}\n"
                        response += f"Content: {chunk['text'][:200]}...\n"  # Show first 200 chars
                
                return response
            
            # For other queries, create a standard response with text chunks
            basic_response = ""
            
            # Employees information
            if search_results.get("employees"):
                employees_info = "\n".join([
                    f"- {employee.get('name', 'Unknown')}: {employee.get('role', 'No role specified')}" 
                    for employee in search_results.get("employees", [])
                ])
                basic_response = f"Found information about the following employees:\n{employees_info}"
            
            # Projects information
            elif search_results.get("projects"):
                projects_info = "\n".join([
                    f"- {project.get('name', 'Unknown')}: Located in {project.get('location', 'Unknown location')}" 
                    for project in search_results.get("projects", [])
                ])
                basic_response = f"Found information about the following projects:\n{projects_info}"
            
            # Add text chunks section
            if search_results.get("documents") or search_results.get("semantic_results"):
                text_chunks = []
                
                # Add text chunks from direct document search
                for doc in search_results.get("documents", []):
                    if "text" in doc:
                        text_chunks.append({
                            "text": doc["text"],
                            "text_id": doc.get("text_id", "Unknown"),
                            "document_link": doc.get("document_link", "Not available")
                        })
                
                # Add text chunks from semantic search
                for doc in search_results.get("semantic_results", []):
                    if "text" in doc:
                        text_chunks.append({
                            "text": doc["text"],
                            "text_id": doc.get("text_id", "Unknown"),
                            "document_link": doc.get("document_link", "Not available")
                        })
                
                if text_chunks:
                    if basic_response:
                        basic_response += "\n\n"
                    
                    basic_response += "RELEVANT TEXT CHUNKS:\n"
                    # Limit to 3 most relevant chunks to keep response concise
                    for i, chunk in enumerate(text_chunks[:3], 1):
                        basic_response += f"\n{i}. Text ID: {chunk['text_id']}\n"
                        basic_response += f"Source: {chunk['document_link']}\n"
                        basic_response += f"Content: {chunk['text'][:200]}...\n"  # Show first 200 chars
            
            if not basic_response:
                basic_response = f"I couldn't find specific information to answer your query: '{query}'."
            
            return basic_response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Error generating response: {str(e)}"


def get_document_link(document_id: str) -> str:
    """Get a document's link from documents table"""
    if not supabase:
        return "Document link not available"
    
    try:
        document = supabase.table('documents').select('document_link, pdf_name').eq('id', document_id).execute()
        
        if document.data and len(document.data) > 0:
            link = document.data[0].get('document_link', 'Link not available')
            name = document.data[0].get('pdf_name', 'Unnamed document')
            return f"{name} ({link})"
        else:
            return "Document link not available"
    except Exception as e:
        logger.error(f"Error getting document link: {e}")
        return "Error retrieving document link"


def execute_search(query: str) -> Dict[str, Any]:
    """Execute a search based on the natural language query"""
    if not verify_environment():
        return {"error": "Environment not properly configured"}
    
    # Analyze the query to determine what to search for
    analysis = analyze_query(query)
    query_type = analysis.get("type", "unknown")
    entities = analysis.get("entities", [])
    key_terms = analysis.get("key_terms", [])
    
    logger.info(f"Query type: {query_type}")
    logger.info(f"Entities: {entities}")
    logger.info(f"Key terms: {key_terms}")
    
    # Combine entities and key terms for search
    search_terms = entities + key_terms
    search_term = " ".join(search_terms) if search_terms else query
    
    results = {
        "query": query,
        "query_type": query_type,
        "employees": [],
        "projects": [],
        "employee_projects": [],
        "project_employees": [],
        "documents": [],
        "semantic_results": []
    }
    
    # Execute different searches based on query type
    if query_type == "team_projects":
        # Find the employee first
        employees = search_teams(" ".join(entities))
        results["employees"] = employees
        
        # For each employee, get their projects
        for employee in employees:
            employee_projects = get_team_projects(employee["id"])
            if employee_projects:
                results["employee_projects"].append({
                    "employee_id": employee["id"],
                    "employee_name": employee["name"],
                    "employee_role": employee.get("role", ""),
                    "projects": employee_projects
                })
                
                # Get relevant text chunks for this employee
                text_contents = get_relevant_text_for_employee(employee["id"])
                if text_contents:
                    # Avoid duplicates
                    existing_text_ids = {doc.get('text_id') for doc in results["documents"]}
                    for text in text_contents:
                        if text.get('text_id') not in existing_text_ids:
                            results["documents"].append(text)
                            existing_text_ids.add(text.get('text_id'))
    
    elif query_type == "team_info" or query_type == "general":
        # Search for employee information
        employees = search_teams(search_term)
        results["employees"] = employees
        
        # For each employee, get both their projects and relevant text
        for employee in employees:
            # Get projects
            employee_projects = get_team_projects(employee["id"])
            if employee_projects:
                results["employee_projects"].append({
                    "employee_id": employee["id"],
                    "employee_name": employee["name"],
                    "employee_role": employee.get("role", ""),
                    "projects": employee_projects
                })
            
            # Get only relevant text chunks for this employee
            text_contents = get_relevant_text_for_employee(employee["id"])
            if text_contents:
                # Avoid duplicates
                existing_text_ids = {doc.get('text_id') for doc in results["documents"]}
                for text in text_contents:
                    if text.get('text_id') not in existing_text_ids:
                        results["documents"].append(text)
                        existing_text_ids.add(text.get('text_id'))
    
    elif query_type == "project_info" or query_type == "general":
        # Search for project information
        projects = search_projects(search_term)
        results["projects"] = projects
        
        # For each project, get the employees and relevant text
        for project in projects:
            # Get employees
            project_employees = get_project_teams(project["id"])
            if project_employees:
                results["project_employees"].append({
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "project_location": project.get("location", ""),
                    "employees": project_employees
                })
            
            # Get only relevant text chunks for this project
            text_contents = get_relevant_text_for_project(project["id"])
            if text_contents:
                # Avoid duplicates
                existing_text_ids = {doc.get('text_id') for doc in results["documents"]}
                for text in text_contents:
                    if text.get('text_id') not in existing_text_ids:
                        results["documents"].append(text)
                        existing_text_ids.add(text.get('text_id'))
    
    elif query_type == "project_teams":
        # Find the project first
        projects = search_projects(" ".join(entities))
        results["projects"] = projects
        
        # Get employees for each project
        for project in projects:
            project_employees = get_project_teams(project["id"])
            if project_employees:
                results["project_employees"].append({
                    "project_id": project["id"],
                    "project_name": project["name"],
                    "project_location": project.get("location", ""),
                    "employees": project_employees
                })
            
            # Get only relevant text chunks for this project
            text_contents = get_relevant_text_for_project(project["id"])
            if text_contents:
                # Avoid duplicates
                existing_text_ids = {doc.get('text_id') for doc in results["documents"]}
                for text in text_contents:
                    if text.get('text_id') not in existing_text_ids:
                        results["documents"].append(text)
                        existing_text_ids.add(text.get('text_id'))
    
    # For specialized searches like role-based or domain-based, enhance with semantic search
    if "role" in query.lower() or any(domain in query.lower() for domain in ["airport", "sewage", "hydraulic", "civil", "structural"]):
        # Perform targeted semantic search using the query
        semantic_results = search_semantically(query)
        
        # Filter any semantic results if we have text contexts from employees or projects
        if results["documents"] and semantic_results:
            # Keep semantic results that might be related to our specific context
            filtered_semantic = []
            existing_document_ids = {doc.get('document_id') for doc in results["documents"] if doc.get('document_id')}
            
            for result in semantic_results:
                # Include results from the same documents or with high similarity
                if (result.get('document_id') in existing_document_ids or 
                    result.get('similarity', 0) > 0.7):
                    filtered_semantic.append(result)
            
            results["semantic_results"] = filtered_semantic
        else:
            # If no document context, use all semantic results
            results["semantic_results"] = semantic_results
    
    return results


def main():
    """Main function to run the search engine from the command line"""
    parser = argparse.ArgumentParser(description="Search engine for teams and projects")
    parser.add_argument("query", help="Natural language query", nargs="+")
    args = parser.parse_args()
    
    # Combine all arguments into a single query string
    query = " ".join(args.query)
    
    # Verify environment
    if not verify_environment():
        logger.error("Environment not properly configured")
        sys.exit(1)
    
    # Execute search
    logger.info(f"Executing search: {query}")
    results = execute_search(query)
    
    # Generate response
    response = generate_response(results, query)
    
    # Print the response
    print("\n" + "="*80)
    print("SEARCH RESPONSE")
    print("="*80)
    print(response)
    print("="*80 + "\n")


if __name__ == "__main__":
    main() 
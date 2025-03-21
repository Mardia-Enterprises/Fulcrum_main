import os
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from supabase import create_client
from dotenv import load_dotenv

# Import models
from models import ProjectResponse, ProjectDetail, ProjectUpdate, ProjectCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("database")

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

def format_project_data(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format project data for response
    """
    # Copy the original data to avoid modifying it
    formatted_data = dict(project_data)
    
    # Create ID from title if not present
    if 'id' not in formatted_data and 'title_and_location' in formatted_data:
        title = formatted_data['title_and_location']
        formatted_data['id'] = title.lower().replace(' ', '_').replace(',', '').replace('.', '')[:50]
    
    # Ensure required fields exist
    if 'year_completed' not in formatted_data:
        formatted_data['year_completed'] = {
            "professional_services": "Unknown",
            "construction": "Unknown"
        }
    
    # Return formatted data
    return formatted_data

def get_all_projects() -> List[ProjectResponse]:
    """
    Retrieve all projects from Supabase
    """
    try:
        # Directly query all projects from the projects table
        logger.info("Querying Supabase for all projects")
        result = supabase.table('projects').select('id, title, project_data').execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching projects from Supabase: {result.error}")
            return []
        
        logger.info(f"Found {len(result.data)} projects")
        
        projects = []
        for item in result.data:
            project_data = item.get('project_data', {})
            
            # Create project response
            projects.append(
                ProjectResponse(
                    id=item.get('id', ''),
                    title_and_location=project_data.get('title_and_location', 'Unknown'),
                    project_owner=project_data.get('project_owner', 'Unknown'),
                    score=1.0  # Default score for direct retrieval
                )
            )
        
        return projects
    
    except Exception as e:
        logger.error(f"Error retrieving all projects: {str(e)}")
        return []

def get_project_by_id(project_id: str) -> Optional[ProjectDetail]:
    """
    Retrieve a specific project by ID
    """
    try:
        logger.info(f"Retrieving project with ID: {project_id}")
        
        # Query Supabase for the project
        result = supabase.table('projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching project from Supabase: {result.error}")
            return None
        
        if not result.data:
            logger.warning(f"Project with ID '{project_id}' not found")
            return None
        
        # Get project data
        project_item = result.data[0]
        project_data = project_item.get('project_data', {})
        
        # Format project data for response
        formatted_data = format_project_data(project_data)
        formatted_data['id'] = project_id
        
        # Validate all required fields are present with correct types
        logger.info(f"Project data structure: {formatted_data.keys()}")
        
        # Ensure firms_from_section_c is a list of objects with the right structure
        if 'firms_from_section_c' in formatted_data:
            firms = formatted_data['firms_from_section_c']
            if not isinstance(firms, list):
                formatted_data['firms_from_section_c'] = []
            else:
                # Validate each firm has the required structure
                for i, firm in enumerate(firms):
                    if not isinstance(firm, dict):
                        firms[i] = {"firm_name": "Unknown", "firm_location": "Unknown", "role": "Unknown"}
                    else:
                        # Ensure required fields exist
                        for field in ['firm_name', 'firm_location', 'role']:
                            if field not in firm or not firm[field]:
                                firm[field] = "Unknown"
        else:
            formatted_data['firms_from_section_c'] = []
        
        # Ensure year_completed has the right structure
        if 'year_completed' not in formatted_data or not isinstance(formatted_data['year_completed'], dict):
            formatted_data['year_completed'] = {
                'professional_services': None,
                'construction': None
            }
        else:
            # Ensure both fields exist
            if 'professional_services' not in formatted_data['year_completed']:
                formatted_data['year_completed']['professional_services'] = None
            if 'construction' not in formatted_data['year_completed']:
                formatted_data['year_completed']['construction'] = None
        
        # Ensure all other required fields are present
        required_fields = [
            'title_and_location', 
            'project_owner', 
            'point_of_contact_name', 
            'point_of_contact', 
            'brief_description'
        ]
        
        for field in required_fields:
            if field not in formatted_data or not formatted_data[field]:
                formatted_data[field] = "Unknown" if field != 'brief_description' else "No description available"
        
        logger.info(f"Returning project data with fields: {', '.join(formatted_data.keys())}")
        
        # Create project detail response
        return ProjectDetail(**formatted_data)
    
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        return None

def update_project(project_id: str, project_update: ProjectUpdate) -> Optional[ProjectDetail]:
    """
    Update an existing project
    """
    try:
        logger.info(f"Updating project with ID: {project_id}")
        
        # First, get the existing project
        result = supabase.table('projects').select('*').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching project from Supabase: {result.error}")
            return None
        
        if not result.data:
            logger.warning(f"Project with ID '{project_id}' not found")
            return None
        
        # Get existing project data
        project_item = result.data[0]
        existing_project_data = project_item.get('project_data', {})
        
        # Convert to dict for updating
        update_data = project_update.dict(exclude_unset=True)
        
        # Update only the fields that are provided
        for key, value in update_data.items():
            if value is not None:
                existing_project_data[key] = value
        
        # Update in Supabase - we need to regenerate embeddings
        from resume_parser_f.datauploader import upsert_project_in_supabase
        
        # Get title for the update operation
        title = existing_project_data.get('title_and_location', 'Unknown Project')
        
        # Update project using the uploader function which will handle embeddings
        upsert_project_in_supabase(project_id, title, existing_project_data)
        
        # Return updated project
        formatted_data = format_project_data(existing_project_data)
        formatted_data['id'] = project_id
        
        return ProjectDetail(**formatted_data)
    
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        return None

def delete_project(project_id: str) -> bool:
    """
    Delete a project by ID
    """
    try:
        logger.info(f"Deleting project with ID: {project_id}")
        
        # Delete from Supabase
        result = supabase.table('projects').delete().eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error deleting project from Supabase: {result.error}")
            return False
        
        if not result.data:
            logger.warning(f"Project with ID '{project_id}' not found or already deleted")
            return False
        
        logger.info(f"Successfully deleted project with ID: {project_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        return False

def create_project(project_create: ProjectCreate) -> Optional[ProjectDetail]:
    """
    Create a new project
    """
    try:
        logger.info("Creating new project")
        
        # Convert to dict for processing
        project_data = project_create.dict()
        
        # Generate a project ID from the title
        title = project_data.get('title_and_location', 'Unknown Project')
        project_id = title.lower().replace(' ', '_').replace(',', '').replace('.', '')[:50]
        
        # Check if ID already exists to avoid conflicts
        result = supabase.table('projects').select('id').eq('id', project_id).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error checking for existing project: {result.error}")
            return None
        
        if result.data:
            # If ID already exists, append a UUID to make it unique
            project_id = f"{project_id}_{str(uuid.uuid4())[:8]}"
        
        # Use the uploader function to create the project with embeddings
        from resume_parser_f.datauploader import upsert_project_in_supabase
        upsert_project_in_supabase(project_id, title, project_data)
        
        # Return created project
        project_data['id'] = project_id
        
        return ProjectDetail(**project_data)
    
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return None

def text_search_by_project_owner(owner_text: str) -> List[ProjectResponse]:
    """
    Perform a direct text search for projects by owner with fuzzy matching
    """
    try:
        logger.info(f"Performing direct text search for projects with owner containing: '{owner_text}'")
        
        # Expand common abbreviations and alternate names
        owner_variations = [owner_text]
        
        # Handle common abbreviations and variations
        if owner_text.lower() == "usace":
            owner_variations.extend([
                "U.S. Army Corps of Engineers", 
                "US Army Corps of Engineers",
                "Army Corps of Engineers",
                "Corps of Engineers"
            ])
        elif owner_text.lower() == "fort worth":
            owner_variations.extend([
                "Fort Worth District",
                "USACE Fort Worth"
            ])
        
        logger.info(f"Using owner variations: {owner_variations}")
        
        # Fetch all projects to do text matching
        result = supabase.table('projects').select('id, title, project_data').execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching projects from Supabase: {result.error}")
            return []
        
        # Search for matches with project owner
        matches = []
        for item in result.data:
            project_data = item.get('project_data', {})
            project_owner = project_data.get('project_owner', '')
            
            # Check if any variation is in the project owner field
            for variation in owner_variations:
                if variation.lower() in project_owner.lower():
                    # Found a match
                    matches.append(
                        ProjectResponse(
                            id=item.get('id', ''),
                            title_and_location=project_data.get('title_and_location', 'Unknown'),
                            project_owner=project_owner,
                            score=1.0  # High score for direct text match
                        )
                    )
                    # Break the inner loop once a match is found
                    break
            
            # Even if no exact matches, try fuzzy matching for close matches
            if not any(variation.lower() in project_owner.lower() for variation in owner_variations):
                # Check for partial word matches (e.g., "Fort" matches "Fort Worth District")
                words_in_owner = owner_text.lower().split()
                project_owner_lower = project_owner.lower()
                
                # Count how many words match
                matching_words = sum(1 for word in words_in_owner if word in project_owner_lower)
                
                # If at least one word matches, consider it a partial match
                if matching_words > 0 and len(words_in_owner) > 0:
                    match_score = matching_words / len(words_in_owner)  # Score based on proportion of matching words
                    if match_score >= 0.5:  # At least half the words match
                        matches.append(
                            ProjectResponse(
                                id=item.get('id', ''),
                                title_and_location=project_data.get('title_and_location', 'Unknown'),
                                project_owner=project_owner,
                                score=match_score  # Partial match score
                            )
                        )
        
        # Sort by score
        matches.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Found {len(matches)} projects with owner containing '{owner_text}' or variations")
        return matches
        
    except Exception as e:
        logger.error(f"Error in text search by project owner: {str(e)}")
        return []

def query_projects(query_text: str, limit: int = 10) -> List[ProjectResponse]:
    """
    Query projects using semantic search with enhanced OpenAI embeddings
    """
    try:
        logger.info(f"Querying projects with: '{query_text}'")
        
        # First check if we're looking for a specific owner with simple text matching
        if "owner" in query_text.lower() or "client" in query_text.lower():
            # Extract potential owner names for direct matching
            potential_owners = []
            
            # Common organizations that might be searched for
            orgs = ["USACE", "Army Corps", "Corps of Engineers", "Fort Worth", "District"]
            
            # Check if any of these are in the query
            for org in orgs:
                if org.lower() in query_text.lower():
                    potential_owners.append(org)
            
            if potential_owners:
                logger.info(f"Detected potential owner search for: {potential_owners}")
                
                # Try to find projects with these owners
                all_matches = []
                for owner in potential_owners:
                    owner_matches = text_search_by_project_owner(owner)
                    all_matches.extend(owner_matches)
                
                # If we found projects via direct matching, return them
                if all_matches:
                    # Remove duplicates by using a dictionary with ID as key
                    unique_matches = {}
                    for match in all_matches:
                        unique_matches[match.id] = match
                    
                    # Convert back to list and limit results
                    result_list = list(unique_matches.values())[:limit]
                    logger.info(f"Found {len(result_list)} unique projects via direct owner matching")
                    return result_list
        
        # Try direct text search for USACE if it's in the query regardless of owner keyword
        if "usace" in query_text.lower():
            direct_matches = text_search_by_project_owner("USACE")
            if direct_matches:
                return direct_matches[:limit]
        
        # If direct matching didn't yield results or wasn't appropriate, try semantic search
        try:
            # Import OpenAI embedding function
            from openai import OpenAI
            import numpy as np
            
            # Initialize OpenAI client
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Generate embedding for the query
            logger.info("Generating OpenAI embedding for query")
            response = openai_client.embeddings.create(
                input=query_text,
                model="text-embedding-3-small"  # Latest embedding model
            )
            query_embedding = response.data[0].embedding
            
            # Get all projects from Supabase
            logger.info("Fetching all projects for semantic comparison")
            result = supabase.table('projects').select('id, title, project_data, embedding').execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error fetching projects from Supabase: {result.error}")
                return []
            
            # Calculate similarity for each project manually
            projects_with_scores = []
            
            for item in result.data:
                project_data = item.get('project_data', {})
                embedding = item.get('embedding', [])
                
                if not embedding:
                    logger.warning(f"Project {item.get('id', '')} has no embedding, skipping")
                    continue
                
                # Calculate cosine similarity
                dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
                magnitude_a = sum(a * a for a in query_embedding) ** 0.5
                magnitude_b = sum(b * b for b in embedding) ** 0.5
                similarity = dot_product / (magnitude_a * magnitude_b) if magnitude_a * magnitude_b > 0 else 0
                
                # Use a lower threshold to include more potential matches
                if similarity > 0.1:  # Adjust this threshold as needed
                    projects_with_scores.append({
                        'id': item.get('id', ''),
                        'title_and_location': project_data.get('title_and_location', 'Unknown'),
                        'project_owner': project_data.get('project_owner', 'Unknown'),
                        'similarity': similarity
                    })
            
            # Sort by similarity score (highest first)
            projects_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Take top results based on limit
            top_projects = projects_with_scores[:limit]
            
            logger.info(f"Found {len(top_projects)} projects via semantic search")
            
            # Convert to ProjectResponse objects
            projects = []
            for item in top_projects:
                projects.append(
                    ProjectResponse(
                        id=item['id'],
                        title_and_location=item['title_and_location'],
                        project_owner=item['project_owner'],
                        score=item['similarity']
                    )
                )
            
            return projects
            
        except Exception as e:
            logger.error(f"Error in direct OpenAI embedding search: {str(e)}")
            # Fall back to resume_parser_f implementation if direct approach fails
            
            # Try using existing function from resume_parser_f
            logger.info("Falling back to resume_parser_f query implementation")
            from resume_parser_f.datauploader import query_projects as semantic_query_projects
            results = semantic_query_projects(query_text, top_k=limit)
            
            projects = []
            for item in results:
                project_data = item.get('project_data', {})
                
                projects.append(
                    ProjectResponse(
                        id=item.get('id', ''),
                        title_and_location=project_data.get('title_and_location', 'Unknown'),
                        project_owner=project_data.get('project_owner', 'Unknown'),
                        score=item.get('similarity', 0)
                    )
                )
            
            return projects
    
    except Exception as e:
        logger.error(f"Error querying projects: {str(e)}")
        return [] 
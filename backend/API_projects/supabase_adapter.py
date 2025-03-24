import os
import sys
import logging
import json
from supabase import create_client
from dotenv import load_dotenv
import openai

# Configure logging
from utils import setup_logging
logger = setup_logging()

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

def initialize_supabase():
    """Initialize Supabase client"""
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY must be set in the root .env file")
    
    return create_client(supabase_url, supabase_key)

def ensure_text_search_function():
    """
    Ensures the text search function exists in Supabase.
    This function is called during initialization to create the function if it doesn't exist.
    """
    if not supabase:
        return
    
    try:
        logger.info("Checking for text search function in Supabase")
        
        # SQL for creating the text search function
        sql = """
        -- Function to search for projects using text search
        CREATE OR REPLACE FUNCTION search_projects_text(search_query text)
        RETURNS TABLE (
          id TEXT,
          project_key TEXT,
          file_id TEXT,
          project_data JSONB,
          similarity FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
          RETURN QUERY
          SELECT
            section_f_projects.id,
            section_f_projects.project_key,
            section_f_projects.file_id,
            section_f_projects.project_data,
            0.8 AS similarity  -- Default similarity score for text matches
          FROM section_f_projects
          WHERE 
            -- Search in the project_data jsonb using to_tsvector
            to_tsvector('english', section_f_projects.project_data::text) @@ plainto_tsquery('english', search_query);
        END;
        $$;
        """
        
        # Execute the SQL to create the function
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error creating text search function: {result.error}")
            
            # Try a simpler approach if the exec_sql RPC fails
            try:
                # Execute raw SQL (this requires higher permissions)
                supabase.postgrest.schema('public').execute(sql)
                logger.info("Created text search function using raw SQL")
            except Exception as inner_e:
                logger.error(f"Failed to create text search function with raw SQL: {str(inner_e)}")
                logger.warning("Continuing without text search function - some queries may not work optimally")
        else:
            logger.info("Successfully created or updated text search function")
    
    except Exception as e:
        logger.error(f"Error ensuring text search function: {str(e)}")
        logger.warning("Continuing without text search function - some queries may not work optimally")

# Initialize Supabase client
try:
    supabase = initialize_supabase()
    logger.info("Supabase client initialized successfully")
    
    # Ensure text search function exists
    ensure_text_search_function()
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    supabase = None

def _get_embedding(text):
    """
    Generate an embedding for the given text using OpenAI's API
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        The embedding vector
    """
    try:
        # Check if the OpenAI API key is set
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in the .env file")
            
        # Configure the OpenAI client
        openai.api_key = api_key
        
        # Generate the embedding
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        # Return the embedding vector
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def query_index(query_text, top_k=100, match_threshold=0.01):
    """
    Query the vector store using text and return the top k most similar documents.
    
    Args:
        query_text: The query text to search for
        top_k: The number of documents to return (default: 100)
        match_threshold: The minimum similarity score to consider a match (default: 0.01)
        
    Returns:
        List of dictionaries containing project information
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return []
    
    try:
        # Generate embedding for query
        embedding = _get_embedding(query_text)
        
        # Query the database for semantically similar projects
        logger.info(f"Performing semantic search for: {query_text}")
        result = supabase.rpc(
            'match_section_f_projects',
            {
                'query_embedding': embedding,
                'match_threshold': match_threshold,
                'match_count': top_k
            }
        ).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error in semantic search: {result.error}")
            return []
        
        logger.info(f"Found {len(result.data)} results from semantic search")
        return result.data
    
    except Exception as e:
        logger.error(f"Error in query_index: {str(e)}")
        
        # Fallback to text search if semantic search fails
        try:
            logger.info(f"Falling back to text search for: {query_text}")
            result = supabase.rpc('search_projects_text', {'search_query': query_text}).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Error in text search fallback: {result.error}")
                return []
            
            logger.info(f"Found {len(result.data)} results from text search fallback")
            return result.data
        except Exception as e2:
            logger.error(f"Error in text search fallback: {str(e2)}")
            return []

def fetch_vectors(ids):
    """
    Fetch vectors from Supabase by their IDs
    
    Args:
        ids: List of vector IDs to fetch
        
    Returns:
        List of dictionaries containing project information
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return []
    
    if not ids:
        logger.warning("No IDs provided to fetch_vectors")
        return []
    
    try:
        # Convert list of IDs to a string for the 'in' query
        id_list = ", ".join([f"'{id}'" for id in ids])
        
        # Query the database for the specific vectors
        query = f"id.in.({id_list})"
        result = supabase.table('section_f_projects').select('*').filter(query).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching vectors: {result.error}")
            return []
        
        return result.data
    except Exception as e:
        logger.error(f"Error in fetch_vectors: {str(e)}")
        return []

def delete_vectors(ids):
    """
    Delete vectors from Supabase by their IDs
    
    Args:
        ids: List of vector IDs to delete
        
    Returns:
        True if successful, False otherwise
    """
    if not supabase:
        logger.error("Supabase client not initialized")
        return False
    
    if not ids:
        logger.warning("No IDs provided to delete_vectors")
        return False
    
    try:
        # Convert list of IDs to a string for the 'in' query
        id_list = ", ".join([f"'{id}'" for id in ids])
        
        # Delete the vectors from the database
        query = f"id.in.({id_list})"
        result = supabase.table('section_f_projects').delete().filter(query).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error deleting vectors: {result.error}")
            return False
        
        logger.info(f"Successfully deleted {len(ids)} vectors")
        return True
    except Exception as e:
        logger.error(f"Error in delete_vectors: {str(e)}")
        return False 
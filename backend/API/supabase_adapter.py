import os
import sys
import logging
from supabase import create_client
from dotenv import load_dotenv
import json
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("supabase_adapter")

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

# Initialize Supabase client
try:
    supabase = initialize_supabase()
    logger.info("Supabase client initialized successfully")
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
            model="text-embedding-ada-002"
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
        List of dictionaries containing employee information
    """
    if not supabase:
        initialize_supabase()
    
    try:
        logger.info(f"Querying Supabase for: '{query_text}' (top_k={top_k}, threshold={match_threshold})")
        
        # Generate embedding for the query
        query_embedding = _get_embedding(query_text)
        logger.info(f"Generated embedding with length: {len(query_embedding)}")
        
        # Query Supabase using the match_employees function
        logger.info(f"Sending query to Supabase with threshold: {match_threshold}")
        result = supabase.rpc(
            'match_employees',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'match_count': top_k
            }
        ).execute()
        
        logger.info(f"Raw result data count: {len(result.data)}")
        if len(result.data) > 0:
            logger.info(f"First raw result similarity: {result.data[0].get('similarity', 0)}")
        
        # Process the results
        matches = []
        for item in result.data:
            resume_data = item.get('resume_data', {})
            
            # Handle the capitalization variations in field names
            name = None
            # Try different capitalization patterns for name
            if 'name' in resume_data:
                name = resume_data['name']
            elif 'Name' in resume_data:
                name = resume_data['Name']
            else:
                # Use ID as fallback
                name = item.get('id', '').replace('_', ' ').title()
            
            # Extract role field considering different capitalization
            role = None
            if 'role' in resume_data:
                role = resume_data['role']
            elif 'Role' in resume_data:
                role = resume_data['Role']
            elif 'Role in Contract' in resume_data:
                role = resume_data['Role in Contract']
            else:
                role = []
            
            # Log extracted fields for debugging
            logger.info(f"Extracted employee: {name} with role: {role}")
            
            # Extract relevant information from resume_data with proper field names and fallbacks
            employee_info = {
                'id': item.get('id', ''),
                'name': name,
                'role': role,
                'education': resume_data.get('education', resume_data.get('Education', [])),
                'years_experience': resume_data.get('years_experience', 
                                       resume_data.get('Years of Experience', 
                                       resume_data.get('years of experience', 'Not provided'))),
                'firm_name_and_location': resume_data.get('firm_name_and_location', 
                                         resume_data.get('Firm Name & Location', {})),
                'current_professional_registration': resume_data.get('current_professional_registration', 
                                                   resume_data.get('Professional Registrations', [])),
                'other_professional_qualifications': resume_data.get('other_professional_qualifications', 
                                                  resume_data.get('Other Professional Qualifications', '')),
                'relevant_projects': resume_data.get('relevant_projects', 
                                    resume_data.get('Relevant Projects', [])),
                'score': item.get('similarity', 0)
            }
            
            matches.append(employee_info)
        
        logger.info(f"Found {len(matches)} matches")
        if matches:
            # Log the first match details for debugging
            first_match = matches[0]
            logger.info(f"Best match: {first_match.get('name')} with score {first_match.get('score')}")
        
        return matches
    
    except Exception as e:
        logger.error(f"Error querying Supabase: {str(e)}")
        return []

def fetch_vectors(ids):
    """
    Fetch vectors by IDs from Supabase
    
    Args:
        ids: List of vector IDs to fetch
    
    Returns:
        An object with vectors that include id, metadata, and values
    """
    if not supabase:
        initialize_supabase()
    
    try:
        logger.info(f"Fetching vectors from Supabase for IDs: {ids}")
        
        # Fetch vectors by ID
        result = supabase.table('employees').select('*').in_('id', ids).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error fetching vectors from Supabase: {result.error}")
            raise Exception(f"Supabase fetch error: {result.error}")
        
        logger.info(f"Fetched {len(result.data)} records from Supabase")
        
        # Detailed logging of raw data for debugging
        if result.data:
            logger.info(f"Raw data for first record: {json.dumps(result.data[0], indent=2)}")
        
        # Format results to match Pinecone's response structure
        vectors = {}
        for item in result.data:
            # Log the current item being processed
            item_id = item.get('id', '')
            logger.info(f"Processing vector with ID: {item_id}")
            
            # Extract resume_data for better logs
            resume_data = item.get('resume_data', {})
            logger.info(f"Resume data for {item_id}: {json.dumps(resume_data, indent=2)}")
            
            # Check if resume_data is a string that needs parsing
            if isinstance(resume_data, str):
                try:
                    resume_data = json.loads(resume_data)
                    logger.info("Parsed resume_data from string to JSON")
                except Exception as e:
                    logger.error(f"Failed to parse resume_data string: {e}")
            
            name = resume_data.get('Name', resume_data.get('name', 'Unknown'))
            logger.info(f"Vector contains employee: {name}")
            
            # Store the actual resume_data as string for debugging
            resume_data_str = json.dumps(resume_data)
            
            vector = {
                'id': item_id,
                'metadata': {
                    'resume_data': resume_data_str,
                    'employee_name': item.get('employee_name', name),
                    'file_id': item.get('file_id', '')
                },
                'values': item.get('embedding', [])
            }
            vectors[item_id] = type('Vector', (), vector)  # Convert to object with attributes
        
        # Create a result object similar to Pinecone's
        result_obj = type('FetchResult', (), {'vectors': vectors})
        
        if not vectors:
            logger.warning(f"No vectors found for IDs: {ids}")
        else:
            logger.info(f"Successfully processed {len(vectors)} vectors")
        
        return result_obj
        
    except Exception as e:
        logger.error(f"Error during Supabase fetch: {str(e)}")
        # Return empty result rather than raising, to make the API more resilient
        empty_result = type('FetchResult', (), {'vectors': {}})
        return empty_result

def delete_vectors(ids):
    """
    Delete vectors by IDs from Supabase
    
    Args:
        ids: List of vector IDs to delete
    
    Returns:
        A boolean indicating success or failure
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    
    try:
        # Delete vectors by ID
        result = supabase.table('employees').delete().in_('id', ids).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"Error deleting vectors from Supabase: {result.error}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error during Supabase deletion: {str(e)}")
        return False 
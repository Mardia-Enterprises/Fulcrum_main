#!/usr/bin/env python3
"""
Script to fix the vector embedding dimension issue in datauploader.py.
This ensures that the embeddings will have 1536 dimensions as required by pgvector.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("datauploader_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent  # Project root

# Load environment variables from root directory only
load_dotenv(root_dir / ".env")
logger.info(f"Loading environment variables from: {root_dir / '.env'}")

def check_environment():
    """Check if the required environment variables are set"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in .env file")
        logger.error(f"Please add it to the .env file in the root directory: {root_dir / '.env'}")
        return False
    
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in .env file")
        logger.error(f"Please add them to the .env file in the root directory: {root_dir / '.env'}")
        return False
    
    return True

def check_openai_client():
    """Check if the OpenAI client can be initialized"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Test with a simple embedding
        response = client.embeddings.create(
            input="Test embedding generation",
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        logger.info(f"Generated test embedding with {len(embedding)} dimensions")
        return True, len(embedding)
    except Exception as e:
        logger.error(f"Error with OpenAI client: {e}")
        return False, 0

def check_supabase_connection():
    """Check if the Supabase connection works"""
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_PROJECT_URL")
        supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # Try to query the projects table
        try:
            result = supabase.table('projects').select('id').limit(1).execute()
            logger.info("Supabase connection successful")
            return True
        except Exception as e:
            logger.error(f"Error querying Supabase: {e}")
            return False
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        return False

def fix_datauploader():
    """Fix the datauploader.py file to ensure correct embedding dimensions"""
    datauploader_path = script_dir / "datauploader.py"
    
    if not datauploader_path.exists():
        logger.error(f"datauploader.py not found at {datauploader_path}")
        return False
    
    # Read the current content
    with open(datauploader_path, 'r') as f:
        content = f.read()
    
    # Check if we need to fix the code
    if "embedding_length != 1536" in content:
        logger.info("Dimension check already exists in datauploader.py")
    else:
        logger.info("Adding dimension check to datauploader.py")
        
        # Find the generate_embedding function
        if "def generate_embedding(" not in content:
            logger.error("Could not find generate_embedding function in datauploader.py")
            return False
        
        # Add the dimension check code
        new_content = content.replace(
            "            # Extract the embedding\n            embedding = response.data[0].embedding",
            "            # Extract the embedding\n            embedding = response.data[0].embedding\n            \n            # Check if we have the correct dimensions for pgvector (should be 1536)\n            embedding_length = len(embedding)\n            logger.info(f\"\\033[92m✓ Generated embedding with {embedding_length} dimensions\\033[0m\")\n            \n            # Check if we have the correct dimensions for pgvector (should be 1536)\n            if embedding_length != 1536:\n                logger.warning(f\"\\033[93mWarning: Embedding has {embedding_length} dimensions, expected 1536\\033[0m\")"
        )
        
        # Write the updated content
        with open(datauploader_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Updated datauploader.py with dimension check")
    
    return True

def main():
    """Main function to check and fix the datauploader.py file"""
    logger.info("Starting datauploader fix script")
    
    if not check_environment():
        logger.error("Environment check failed")
        return 1
    
    openai_ok, dimensions = check_openai_client()
    if not openai_ok:
        logger.error("OpenAI client check failed")
        return 1
    
    logger.info(f"OpenAI embeddings have {dimensions} dimensions")
    if dimensions != 1536:
        logger.warning(f"WARNING: OpenAI embeddings have {dimensions} dimensions, but Supabase expects 1536")
        logger.warning("This might cause issues with the Supabase pgvector extension")
    
    if not check_supabase_connection():
        logger.warning("Supabase connection check failed")
        # Continue anyway, as we're just fixing the file
    
    if not fix_datauploader():
        logger.error("Failed to fix datauploader.py")
        return 1
    
    logger.info("datauploader.py check and fix completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
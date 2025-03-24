import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

def setup_logging():
    """Configure and return a logger instance"""
    logger = logging.getLogger("api_projects")
    logger.setLevel(logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger = setup_logging()
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger = setup_logging()
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

def generate_embedding(text):
    """Generate embedding vector for the provided text using OpenAI's API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set in the .env file")
        return None
        
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None 
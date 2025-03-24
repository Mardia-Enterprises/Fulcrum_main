import os
import sys
import uvicorn
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("run_api")

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

def run_server():
    """Run the FastAPI server"""
    # Get the port from environment variable if set, otherwise use default
    port = int(os.getenv("API_PROJECTS_PORT", "8001"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting Project API server on {host}:{port}")
    
    # Run the server
    if __package__ is None:
        # Running directly
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True
        )
    else:
        # Running as a module
        uvicorn.run(
            "API_projects.main:app",
            host=host,
            port=port,
            reload=True
        )

if __name__ == "__main__":
    run_server() 
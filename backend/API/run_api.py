#!/usr/bin/env python
"""
API Runner script that properly sets up the Python path
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables from the root .env file
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: Root .env file not found at {env_path}. Using system environment variables.")

# Check if required environment variables are set
required_vars = ["OPENAI_API_KEY", "SUPABASE_PROJECT_URL", "SUPABASE_PRIVATE_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"Error: The following required environment variables are not set: {', '.join(missing_vars)}")
    print("Please set these variables in your .env file or system environment before running the API.")
    sys.exit(1)

# Run the API server
if __name__ == "__main__":
    print("Starting API server...")
    print("API will be available at http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
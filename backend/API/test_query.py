#!/usr/bin/env python
"""
Test script to directly query Supabase
"""
import os
import sys
import json
from colorama import init, Fore, Style
from dotenv import load_dotenv
import supabase_adapter
from supabase import create_client
from utils import generate_embedding

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Colors for console output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_color(text, color):
    print(f"{color}{text}{NC}")

# Load environment variables from the root .env file
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print_color(f"✓ Loaded environment variables from {env_path}", GREEN)
else:
    print_color(f"! Root .env file not found at {env_path}. Using system environment variables.", YELLOW)

# Try to connect to Supabase
try:
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    supabase = create_client(supabase_url, supabase_key)
    print_color("✓ Successfully connected to Supabase", GREEN)
    
    # Test query 1: Get all employees
    print_color("\nTest 1: Listing all employees directly from Supabase", GREEN)
    result = supabase.table('employees').select('*').execute()
    print_color(f"Found {len(result.data)} employees", GREEN)
    
    # Test query 2: Search for "project manager" with a much lower threshold
    print_color("\nTest 2: Searching for 'project manager' directly with embedding (low threshold)", GREEN)
    query_embedding = generate_embedding("project manager")
    vector_result = supabase.rpc(
        'match_employees',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.1,  # Much lower threshold
            'match_count': 10
        }
    ).execute()
    
    print_color(f"Found {len(vector_result.data)} matches", GREEN)
    if vector_result.data:
        print_color("\nFirst match raw data:", YELLOW)
        print(json.dumps(vector_result.data[0], indent=2))
        
    for i, match in enumerate(vector_result.data):
        print_color(f"\nMatch {i+1} (similarity: {match.get('similarity', 0):.3f}):", GREEN)
        employee_data = match.get('resume_data', {})
        print(f"Name: {employee_data.get('Name', 'Unknown')}")
        print(f"name: {employee_data.get('name', 'Unknown')}")  # Try lowercase
        print(f"Role: {employee_data.get('Role in Contract', 'Not provided')}")
        print(f"role: {employee_data.get('role', 'Not provided')}")  # Try lowercase
    
    # Test query 3: Directly use our supabase_adapter with lower threshold
    print_color("\nTest 3: Using our supabase_adapter with lower threshold", GREEN)
    query_result = supabase_adapter.query_index(
        query_text="project manager",
        top_k=10,
        match_threshold=0.1  # Much lower threshold
    )
    
    print_color(f"Found {len(query_result)} matches via adapter", GREEN)
    
    for i, employee in enumerate(query_result):
        print_color(f"\nMatch {i+1} (score: {employee.get('score', 0):.3f}):", GREEN)
        print(f"Name: {employee.get('name', 'Unknown')}")
        
        # Handle role which could be a list or string
        role = employee.get('role', [])
        if isinstance(role, list):
            role_str = ", ".join(role)
        else:
            role_str = str(role)
        print(f"Role: {role_str}")
    
    # Test query 4: Get employee by ID
    print_color("\nTest 4: Get employee by ID", GREEN)
    # Use the ID from the check_connection.py output
    employee_id = "michael_chopin"
    employee_result = supabase.table('employees').select('*').eq('id', employee_id).execute()
    
    if employee_result.data:
        print_color(f"Found employee with ID {employee_id}", GREEN)
        print_color("\nRaw employee data:", YELLOW)
        print(json.dumps(employee_result.data[0], indent=2))
        
        employee_data = employee_result.data[0].get('resume_data', {})
        print(f"Name: {employee_data.get('Name', 'Unknown')}")
        print(f"name: {employee_data.get('name', 'Unknown')}")  # Try lowercase
        print(f"Role: {employee_data.get('Role in Contract', 'Not provided')}")
        print(f"role: {employee_data.get('role', 'Not provided')}")  # Try lowercase
    else:
        print_color(f"No employee found with ID {employee_id}", YELLOW)

except Exception as e:
    print_color(f"✗ Error during test: {str(e)}", RED)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print_color("\nTest completed", GREEN) 
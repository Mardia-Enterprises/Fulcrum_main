#!/usr/bin/env python
"""
Run this script to extract projects from employee data and add them to the projects database.
This script provides a way to test the project extraction functionality without running the full API.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from root .env file
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(root_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")

# Import the test extraction function
from test_project_extraction import extract_and_create_projects

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Extract projects from employee data and add them to the projects database.')
    parser.add_argument('employee', nargs='?', default=None, help='Employee name (default: all employees)')
    parser.add_argument('--list', action='store_true', help='List all employees')
    parser.add_argument('--test', action='store_true', help='Test mode - do not store projects in Supabase')
    return parser.parse_args()

def list_all_employees():
    """List all employees in the database"""
    # Import employee functions
    from database import get_all_employees
    
    # Get all employees
    employees = get_all_employees()
    if not employees:
        print("No employees found in the database.")
        return
    
    # Print employee names
    print(f"Found {len(employees)} employees in the database:")
    for i, employee in enumerate(employees, 1):
        # Check if employee is a dict-like object or a Pydantic model
        if hasattr(employee, "name"):
            # It's a Pydantic model (EmployeeResponse)
            employee_name = employee.name
        elif hasattr(employee, "get"):
            # It's a dictionary
            employee_name = employee.get("name", "Unknown")
        else:
            # Try direct attribute access as fallback
            try:
                employee_name = employee.name if hasattr(employee, "name") else str(employee)
            except:
                employee_name = "Unknown"
        
        print(f"{i}. {employee_name}")

def process_all_employees(test_mode=False):
    """Process all employees"""
    # Import employee functions
    from database import get_all_employees
    
    # Get all employees
    employees = get_all_employees()
    if not employees:
        print("No employees found in the database.")
        return
    
    total_projects = 0
    successful_employees = 0
    
    # Process each employee
    for employee in employees:
        # Check if employee is a dict-like object or a Pydantic model
        if hasattr(employee, "name"):
            # It's a Pydantic model (EmployeeResponse)
            employee_name = employee.name
        elif hasattr(employee, "get"):
            # It's a dictionary
            employee_name = employee.get("name")
        else:
            # Try direct attribute access as fallback
            try:
                employee_name = employee.name if hasattr(employee, "name") else str(employee)
            except:
                logger.warning(f"Could not extract name from employee: {employee}")
                continue
        
        if not employee_name:
            continue
        
        try:
            print(f"\nProcessing employee: {employee_name}")
            projects = extract_and_create_projects(employee_name)
            print(f"Created {len(projects)} projects for {employee_name}")
            total_projects += len(projects)
            successful_employees += 1
        except Exception as e:
            logger.error(f"Error processing employee {employee_name}: {e}")
    
    print(f"\nSummary: Created {total_projects} projects from {successful_employees} employees")

def main():
    """Main entry point"""
    args = parse_args()
    
    # List all employees if requested
    if args.list:
        list_all_employees()
        return
    
    # Process a specific employee or all employees
    if args.employee:
        print(f"Processing employee: {args.employee}")
        projects = extract_and_create_projects(args.employee)
        print(f"\nCreated {len(projects)} projects for {args.employee}:")
        for project in projects:
            print(f"- {project['title']} (ID: {project['project_id']})")
    else:
        print("Processing all employees...")
        process_all_employees(args.test)

if __name__ == "__main__":
    main() 
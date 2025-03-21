#!/usr/bin/env python3
"""
Debug script for Supabase connectivity issues.
This script tests the connection to Supabase and attempts to insert a test record.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv
import uuid

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent  # Project root

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

# Check for Supabase API keys
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")

if not supabase_url or not supabase_key:
    print("\033[91mError: SUPABASE_PROJECT_URL or SUPABASE_PRIVATE_API_KEY not found in .env file\033[0m")
    print("Please add your Supabase credentials to the .env file in the root directory")
    print("Example:")
    print("SUPABASE_PROJECT_URL=https://your-project-id.supabase.co")
    print("SUPABASE_PRIVATE_API_KEY=your-api-key-here")
    sys.exit(1)

print("\033[92m✓ Supabase credentials found in environment variables\033[0m")
print(f"URL: {supabase_url}")
# Only show first and last few characters of the key for security
masked_key = supabase_key[:4] + "*" * (len(supabase_key) - 8) + supabase_key[-4:]
print(f"API Key: {masked_key}")

# Initialize Supabase client
try:
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)
    print("\033[92m✓ Supabase client initialized\033[0m")
except Exception as e:
    print(f"\033[91mError initializing Supabase client: {str(e)}\033[0m")
    sys.exit(1)

def test_connection():
    """Test basic connection to Supabase"""
    print("\n\033[94mTesting Supabase connection...\033[0m")
    
    try:
        # Simple ping query - get service status
        print("Checking if we can connect to the Supabase service...")
        
        # Try to access service health
        import requests
        health_url = f"{supabase_url}/rest/v1/"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        
        response = requests.get(health_url, headers=headers)
        
        if response.status_code == 200:
            print("\033[92m✓ Successfully connected to Supabase REST API\033[0m")
            print(f"Status code: {response.status_code}")
            return True
        else:
            print(f"\033[91mError connecting to Supabase: Status code {response.status_code}\033[0m")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"\033[91mError connecting to Supabase: {str(e)}\033[0m")
        traceback.print_exc()
        return False

def check_table_exists():
    """Check if the projects table exists"""
    print("\n\033[94mChecking if 'projects' table exists...\033[0m")
    
    try:
        # Try to query a single row to check if table exists
        result = supabase.table('projects').select('*').limit(1).execute()
        print("\033[92m✓ Table 'projects' exists\033[0m")
        
        # Check if we got any data
        if result.data:
            print(f"Found {len(result.data)} existing records")
            if len(result.data) > 0:
                print("Sample record ID:", result.data[0].get('id', 'unknown'))
        else:
            print("Table exists but is empty")
        
        return True
    except Exception as e:
        if "relation \"projects\" does not exist" in str(e).lower():
            print("\033[91m✗ Table 'projects' does not exist\033[0m")
            print("You need to run the SQL setup script to create the table")
            print("See instructions in backend/resume_parser_f/supabase_setup.sql")
        else:
            print(f"\033[91mError checking table: {str(e)}\033[0m")
            traceback.print_exc()
        return False

def test_insert():
    """Test inserting a record into the projects table"""
    print("\n\033[94mTesting record insertion...\033[0m")
    
    # Create a unique test ID
    test_id = f"test_{uuid.uuid4().hex[:8]}"
    
    # Create test data
    test_data = {
        'id': test_id,
        'title': 'Test Project',
        'project_data': {
            'title_and_location': 'Test Project, Test Location',
            'year_completed': {'professional_services': 2023, 'construction': None},
            'project_owner': 'Test Owner',
            'point_of_contact_name': 'Test Contact',
            'point_of_contact': '555-1234',
            'brief_description': 'This is a test project for debugging purposes',
            'firms_from_section_c': [
                {'firm_name': 'Test Firm', 'firm_location': 'Test City, ST', 'role': 'Test Role'}
            ]
        },
        'embedding': [0.1] * 1536  # Use full 1536 dimensions required by pgvector
    }
    
    try:
        print(f"Inserting test record with ID: {test_id}...")
        result = supabase.table('projects').insert(test_data).execute()
        
        if hasattr(result, 'error') and result.error:
            print(f"\033[91mInsertion failed: {result.error}\033[0m")
            return False
        else:
            print("\033[92m✓ Test record inserted successfully\033[0m")
            
            # Now try to retrieve it
            print("Verifying record was inserted by retrieving it...")
            verification = supabase.table('projects').select('*').eq('id', test_id).execute()
            
            if verification.data and len(verification.data) > 0:
                print("\033[92m✓ Record retrieved successfully\033[0m")
                
                # Clean up - delete the test record
                print("Cleaning up - deleting test record...")
                supabase.table('projects').delete().eq('id', test_id).execute()
                print("\033[92m✓ Test record deleted\033[0m")
                
                return True
            else:
                print("\033[91mRecord was not found after insertion\033[0m")
                return False
    except Exception as e:
        print(f"\033[91mError during test insertion: {str(e)}\033[0m")
        traceback.print_exc()
        return False

def test_embedding_insertion():
    """Test inserting a record with a realistic embedding"""
    print("\n\033[94mTesting embedding insertion...\033[0m")
    
    # First check if we can access OpenAI
    try:
        from openai import OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai_api_key:
            print("\033[91mError: OPENAI_API_KEY not found in environment variables\033[0m")
            print("Skipping embedding test")
            return False
        
        print("Initializing OpenAI client...")
        openai_client = OpenAI(api_key=openai_api_key)
        
        # Create a unique test ID
        test_id = f"embed_test_{uuid.uuid4().hex[:8]}"
        
        # Generate an actual embedding
        print("Generating embedding with OpenAI...")
        try:
            response = openai_client.embeddings.create(
                input="This is a test project for Supabase insertion debugging",
                model="text-embedding-3-small"
            )
            
            embedding = response.data[0].embedding
            embedding_length = len(embedding)
            print(f"\033[92m✓ Generated embedding with {embedding_length} dimensions\033[0m")
            
            # Create test data with the real embedding
            test_data = {
                'id': test_id,
                'title': 'Embedding Test Project',
                'project_data': {
                    'title_and_location': 'Embedding Test Project, Test Location',
                    'year_completed': {'professional_services': 2023, 'construction': None},
                    'project_owner': 'Test Owner',
                    'point_of_contact_name': 'Test Contact',
                    'point_of_contact': '555-1234',
                    'brief_description': 'This is a test project with a real embedding',
                    'firms_from_section_c': []
                },
                'embedding': embedding
            }
            
            # Try to insert it
            print("Inserting record with real embedding...")
            result = supabase.table('projects').insert(test_data).execute()
            
            if hasattr(result, 'error') and result.error:
                print(f"\033[91mInsertion with embedding failed: {result.error}\033[0m")
                return False
            else:
                print("\033[92m✓ Record with embedding inserted successfully\033[0m")
                
                # Clean up
                print("Cleaning up - deleting test record...")
                supabase.table('projects').delete().eq('id', test_id).execute()
                print("\033[92m✓ Test record deleted\033[0m")
                return True
                
        except Exception as e:
            print(f"\033[91mError generating or inserting embedding: {str(e)}\033[0m")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"\033[91mError initializing OpenAI client: {str(e)}\033[0m")
        traceback.print_exc()
        return False

def run_sql_query(query):
    """Run a raw SQL query for debugging"""
    try:
        result = supabase.table('projects').select('*').execute()
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def test_real_pdf_processing():
    """Test processing a real PDF if available"""
    print("\n\033[94mChecking for PDFs to test full processing...\033[0m")
    
    # Check for PDFs in the test_pdfs directory
    test_pdfs_dir = script_dir / "resume_parser_f" / "test_pdfs"
    if not test_pdfs_dir.exists():
        print(f"Test PDFs directory not found at {test_pdfs_dir}")
        print("Skipping full PDF processing test")
        return False
    
    pdf_files = list(test_pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {test_pdfs_dir}")
        print("Please add test PDFs to run a full processing test")
        return False
    
    # Use the first PDF
    sample_pdf = pdf_files[0]
    print(f"Found test PDF: {sample_pdf.name}")
    
    # Test full processing pipeline
    try:
        print("Testing full processing pipeline with this PDF...")
        
        # Import the processing functions
        sys.path.append(str(script_dir))
        from resume_parser_f.dataparser import extract_structured_data_with_mistral, upload_pdf_to_mistral
        from resume_parser_f.datauploader import upsert_project_in_supabase
        
        # Step 1: Upload to Mistral
        print("Step 1: Uploading PDF to Mistral...")
        try:
            pdf_url = upload_pdf_to_mistral(sample_pdf)
            if not pdf_url:
                print("\033[91mFailed to upload PDF to Mistral\033[0m")
                return False
            print("\033[92m✓ Successfully uploaded PDF to Mistral\033[0m")
            
            # Step 2: Extract data
            print("Step 2: Extracting structured data...")
            project_data = extract_structured_data_with_mistral(pdf_url)
            if not project_data:
                print("\033[91mFailed to extract data from PDF\033[0m")
                return False
            print("\033[92m✓ Successfully extracted structured data\033[0m")
            
            # Print some data for verification
            title = project_data.get('title_and_location', 'Unknown')
            owner = project_data.get('project_owner', 'Unknown')
            print(f"  Title: {title}")
            print(f"  Owner: {owner}")
            
            # Step 3: Upload to Supabase
            print("Step 3: Upserting to Supabase...")
            project_id = f"test_{title.lower().replace(' ', '_').replace(',', '').replace('.', '')[:30]}"
            result = upsert_project_in_supabase(project_id, title, project_data)
            
            if not result:
                print("\033[91mFailed to upsert project to Supabase\033[0m")
                return False
            
            print("\033[92m✓ Successfully uploaded project to Supabase\033[0m")
            print(f"  Project ID: {project_id}")
            
            # Step 4: Verify it's in Supabase
            print("Step 4: Verifying project exists in Supabase...")
            verification = supabase.table('projects').select('id').eq('id', project_id).execute()
            
            if verification.data and len(verification.data) > 0:
                print("\033[92m✓ Project verified in Supabase\033[0m")
                return True
            else:
                print("\033[91mProject not found in Supabase after upload\033[0m")
                return False
            
        except Exception as e:
            print(f"\033[91mError in full processing pipeline: {str(e)}\033[0m")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"\033[91mError setting up full processing test: {str(e)}\033[0m")
        traceback.print_exc()
        return False

def provide_troubleshooting_tips():
    """Provide troubleshooting tips based on test results"""
    print("\n\033[94mTroubleshooting Tips:\033[0m")
    
    print("1. Database Connection Issues:")
    print("   - Verify your Supabase URL and API key in the .env file")
    print("   - Check if you can access the Supabase dashboard in your browser")
    print("   - Ensure the API key has write permissions")
    
    print("\n2. Table Structure Issues:")
    print("   - Run the SQL setup script in resume_parser_f/supabase_setup.sql")
    print("   - Make sure the pgvector extension is enabled")
    print("   - Check that the projects table has all required columns")
    
    print("\n3. Embedding Issues:")
    print("   - Verify your OpenAI API key in the .env file")
    print("   - Check OpenAI API usage limits and billing status")
    print("   - Ensure the embedding vector is compatible with your table structure")
    
    print("\n4. File Processing Issues:")
    print("   - Verify your Mistral API key in the .env file")
    print("   - Check if PDFs are in the correct location (backend/Section F Resumes)")
    print("   - Run the debug_mistral.py script to test PDF processing")
    
    print("\n5. Data Format Issues:")
    print("   - Check the JSON files generated from PDFs for proper structure")
    print("   - Verify that the project data matches the expected format")
    print("   - Look for any null or missing fields that might cause insertion to fail")

def main():
    """Main function to run all diagnostic tests"""
    print("\033[1m\n===== Supabase Diagnostics =====\033[0m")
    
    # Run the tests
    connection_ok = test_connection()
    if not connection_ok:
        print("\033[91mFailed to connect to Supabase. Cannot continue with other tests.\033[0m")
        provide_troubleshooting_tips()
        return 1
    
    table_ok = check_table_exists()
    if not table_ok:
        print("\033[91mProjects table issue. Cannot continue with insertion tests.\033[0m")
        provide_troubleshooting_tips()
        return 1
    
    insert_ok = test_insert()
    if not insert_ok:
        print("\033[91mBasic insert test failed. This needs to be fixed before processing PDFs.\033[0m")
        provide_troubleshooting_tips()
        return 1
    
    embedding_ok = test_embedding_insertion()
    
    # Only run the full PDF processing test if all other tests pass
    if connection_ok and table_ok and insert_ok and embedding_ok:
        print("\n\033[92m✓ All basic tests passed!\033[0m")
        pdf_ok = test_real_pdf_processing()
        
        if not pdf_ok:
            print("\033[91mPDF processing test failed, but database connection is working.\033[0m")
            print("This suggests issues with the PDF processing or Mistral API.")
            provide_troubleshooting_tips()
            return 1
        else:
            print("\n\033[92m✓ All tests passed successfully! Your setup is working correctly.\033[0m")
            return 0
    else:
        print("\n\033[91mSome tests failed. Please fix the issues before processing PDFs.\033[0m")
        provide_troubleshooting_tips()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
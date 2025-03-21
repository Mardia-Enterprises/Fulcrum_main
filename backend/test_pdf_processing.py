#!/usr/bin/env python3
"""
Test script for the PDF processing pipeline.
This script tests the full workflow of processing a PDF, extracting data,
and uploading to Supabase.
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent  # Project root

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - \033[1;33m%(levelname)s\033[0m - %(message)s',
    handlers=[
        logging.FileHandler("pdf_processing_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

def setup_environment():
    """Check if all required environment variables are set"""
    logger.info("\033[1;36mChecking required environment variables...\033[0m")
    
    # Check Mistral API key
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        logger.error("\033[1;31mError: MISTRAL_API_KEY not found in .env file\033[0m")
        return False
    else:
        logger.info("\033[1;32m✓ Found MISTRAL_API_KEY\033[0m")
    
    # Check OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("\033[1;31mError: OPENAI_API_KEY not found in .env file\033[0m")
        return False
    else:
        logger.info("\033[1;32m✓ Found OPENAI_API_KEY\033[0m")
    
    # Check Supabase credentials
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
    if not supabase_url or not supabase_key:
        logger.error("\033[1;31mError: Supabase credentials not found in .env file\033[0m")
        return False
    else:
        logger.info("\033[1;32m✓ Found Supabase credentials\033[0m")
    
    return True

def import_dependencies():
    """Import required dependencies and check if they're installed"""
    logger.info("\033[1;36mImporting required dependencies...\033[0m")
    
    try:
        # Add resume_parser_f to path so we can import modules
        sys.path.append(str(script_dir))
        
        # Import Mistral API modules
        from resume_parser_f.dataparser import extract_structured_data_with_mistral, upload_pdf_to_mistral
        logger.info("\033[1;32m✓ Successfully imported dataparser module\033[0m")
        
        # Import Supabase modules
        from resume_parser_f.datauploader import upsert_project_in_supabase, generate_embedding
        logger.info("\033[1;32m✓ Successfully imported datauploader module\033[0m")
        
        # Test Mistral API client
        try:
            from mistralai.client import MistralClient
            from mistralai.models.chat_completion import ChatMessage
            
            # Check if we have the API key
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                logger.error("\033[1;31mMISTRAL_API_KEY not found in environment variables\033[0m")
                return False
                
            # Initialize the client
            client = MistralClient(api_key=mistral_api_key)
            
            # Just check available models to verify API connection
            models = client.list_models()
            logger.info(f"\033[1;32m✓ Successfully connected to Mistral API: {len(models)} models available\033[0m")
        except Exception as e:
            logger.error(f"\033[1;31mError connecting to Mistral API: {str(e)}\033[0m")
            return False
        
        # Test OpenAI client
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            models = client.models.list()
            logger.info("\033[1;32m✓ Successfully connected to OpenAI API\033[0m")
        except Exception as e:
            logger.error(f"\033[1;31mError connecting to OpenAI API: {str(e)}\033[0m")
            return False
        
        # Test Supabase client
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_PROJECT_URL"),
                os.getenv("SUPABASE_PRIVATE_API_KEY")
            )
            result = supabase.table('projects').select('id').limit(1).execute()
            logger.info("\033[1;32m✓ Successfully connected to Supabase\033[0m")
        except Exception as e:
            logger.error(f"\033[1;31mError connecting to Supabase: {str(e)}\033[0m")
            return False
        
        return True
    except Exception as e:
        logger.error(f"\033[1;31mError importing dependencies: {str(e)}\033[0m")
        logger.error(traceback.format_exc())
        return False

def find_pdf_files(pdf_dir=None):
    """Find PDF files to test"""
    if not pdf_dir:
        # Look in default locations
        pdf_locations = [
            script_dir / "Section F Resumes",
            script_dir / "resume_parser_f" / "test_pdfs",
            root_dir / "Section F Resumes",
            script_dir / "resume_parser_f" / "sample_pdfs"
        ]
        
        for loc in pdf_locations:
            if loc.exists():
                pdf_dir = loc
                break
    else:
        pdf_dir = Path(pdf_dir)
    
    if not pdf_dir or not pdf_dir.exists():
        logger.error("\033[1;31mNo PDF directory found\033[0m")
        return []
    
    logger.info(f"\033[1;36mLooking for PDFs in: {pdf_dir}\033[0m")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"\033[1;33mNo PDF files found in {pdf_dir}\033[0m")
        return []
    
    logger.info(f"\033[1;32m✓ Found {len(pdf_files)} PDF files\033[0m")
    return pdf_files

def test_process_pdf(pdf_path, save_output=True):
    """Process a single PDF file and output detailed diagnostics"""
    logger.info(f"\033[1;36mProcessing PDF: {pdf_path.name}\033[0m")
    
    try:
        # Import required functions
        from resume_parser_f.dataparser import extract_structured_data_with_mistral, upload_pdf_to_mistral
        from resume_parser_f.datauploader import upsert_project_in_supabase
        
        # Step 1: Upload PDF to Mistral
        logger.info("Step 1: Uploading PDF to Mistral...")
        start_time = time.time()
        pdf_url = upload_pdf_to_mistral(pdf_path)
        upload_time = time.time() - start_time
        
        if not pdf_url:
            logger.error("\033[1;31mFailed to upload PDF to Mistral\033[0m")
            return False
        
        logger.info(f"\033[1;32m✓ Successfully uploaded PDF to Mistral (took {upload_time:.2f}s)\033[0m")
        
        # Step 2: Extract structured data
        logger.info("Step 2: Extracting structured data from PDF...")
        start_time = time.time()
        project_data = extract_structured_data_with_mistral(pdf_url)
        extraction_time = time.time() - start_time
        
        if not project_data:
            logger.error("\033[1;31mFailed to extract structured data from PDF\033[0m")
            return False
        
        logger.info(f"\033[1;32m✓ Successfully extracted structured data (took {extraction_time:.2f}s)\033[0m")
        
        # Save extracted data for inspection
        if save_output:
            output_dir = script_dir / "test_outputs"
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"{pdf_path.stem}_extracted.json"
            
            with open(output_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            logger.info(f"Saved extracted data to {output_file}")
        
        # Verify extracted data structure
        logger.info("Verifying extracted data structure...")
        required_fields = [
            'title_and_location', 
            'year_completed', 
            'project_owner', 
            'point_of_contact_name', 
            'point_of_contact', 
            'brief_description', 
            'firms_from_section_c'
        ]
        
        missing_fields = [field for field in required_fields if field not in project_data]
        if missing_fields:
            logger.warning(f"\033[1;33mMissing required fields: {missing_fields}\033[0m")
        else:
            logger.info("\033[1;32m✓ All required fields are present\033[0m")
        
        # Step 3: Upload to Supabase
        logger.info("Step 3: Uploading to Supabase...")
        
        # Generate project ID and title
        title = project_data.get('title_and_location', 'Unknown Project')
        project_id = f"test_{pdf_path.stem.lower().replace(' ', '_').replace('-', '_')}"
        
        # Generate embedding manually so we can measure time
        logger.info("Generating embedding...")
        from resume_parser_f.datauploader import project_to_text, generate_embedding
        project_text = project_to_text(project_data)
        
        start_time = time.time()
        embedding = generate_embedding(project_text)
        embedding_time = time.time() - start_time
        
        if not embedding:
            logger.error("\033[1;31mFailed to generate embedding\033[0m")
        else:
            logger.info(f"\033[1;32m✓ Generated embedding with {len(embedding)} dimensions (took {embedding_time:.2f}s)\033[0m")
        
        # Upload to Supabase
        start_time = time.time()
        result = upsert_project_in_supabase(project_id, title, project_data)
        upload_time = time.time() - start_time
        
        if not result:
            logger.error("\033[1;31mFailed to upload project to Supabase\033[0m")
            return False
        
        logger.info(f"\033[1;32m✓ Successfully uploaded project to Supabase (took {upload_time:.2f}s)\033[0m")
        
        # Step 4: Verify project exists in Supabase
        logger.info("Step 4: Verifying project exists in Supabase...")
        
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_PROJECT_URL"),
                os.getenv("SUPABASE_PRIVATE_API_KEY")
            )
            
            # Try to retrieve the project
            result = supabase.table('projects').select('*').eq('id', project_id).execute()
            
            if not result.data or len(result.data) == 0:
                logger.error("\033[1;31mProject not found in Supabase after upload\033[0m")
                return False
            
            logger.info(f"\033[1;32m✓ Successfully verified project exists in Supabase (ID: {project_id})\033[0m")
            
            # Print some project details
            project = result.data[0]
            logger.info(f"Project title: {project.get('title', 'Unknown')}")
            logger.info(f"Has embedding: {'Yes' if 'embedding' in project and project['embedding'] else 'No'}")
            
            # Clean up test data if needed
            # Uncomment this to delete test projects after verification
            # supabase.table('projects').delete().eq('id', project_id).execute()
            # logger.info(f"Deleted test project from Supabase")
            
            return True
            
        except Exception as e:
            logger.error(f"\033[1;31mError verifying project in Supabase: {str(e)}\033[0m")
            return False
        
    except Exception as e:
        logger.error(f"\033[1;31mError processing PDF: {str(e)}\033[0m")
        logger.error(traceback.format_exc())
        return False

def test_direct_supabase_insert():
    """Test inserting a simple record directly into Supabase"""
    logger.info("\033[1;36mTesting direct Supabase insertion...\033[0m")
    
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_PROJECT_URL"),
            os.getenv("SUPABASE_PRIVATE_API_KEY")
        )
        
        # Create a simple test record
        import uuid
        test_id = f"direct_test_{uuid.uuid4().hex[:8]}"
        test_data = {
            'id': test_id,
            'title': 'Direct Test Project',
            'project_data': {
                'title_and_location': 'Direct Test Project, Test Location',
                'year_completed': {'professional_services': 2023, 'construction': None},
                'project_owner': 'Test Owner',
                'point_of_contact_name': 'Test Contact',
                'point_of_contact': '555-1234',
                'brief_description': 'This is a direct test insertion',
                'firms_from_section_c': []
            },
            'embedding': [0.1] * 1536  # Simple test embedding
        }
        
        # Try to insert
        logger.info(f"Inserting test record with ID: {test_id}...")
        result = supabase.table('projects').insert(test_data).execute()
        
        if hasattr(result, 'error') and result.error:
            logger.error(f"\033[1;31mError inserting test record: {result.error}\033[0m")
            return False
        
        logger.info("\033[1;32m✓ Successfully inserted test record\033[0m")
        
        # Verify the record exists
        verification = supabase.table('projects').select('*').eq('id', test_id).execute()
        
        if not verification.data or len(verification.data) == 0:
            logger.error("\033[1;31mTest record not found after insertion\033[0m")
            return False
        
        logger.info("\033[1;32m✓ Successfully verified test record exists\033[0m")
        
        # Clean up
        logger.info("Cleaning up test record...")
        supabase.table('projects').delete().eq('id', test_id).execute()
        logger.info("\033[1;32m✓ Successfully deleted test record\033[0m")
        
        return True
        
    except Exception as e:
        logger.error(f"\033[1;31mError testing direct Supabase insertion: {str(e)}\033[0m")
        logger.error(traceback.format_exc())
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test PDF processing pipeline')
    parser.add_argument('--pdf', help='Specific PDF file to test')
    parser.add_argument('--dir', help='Directory containing PDF files to test')
    parser.add_argument('--save', action='store_true', default=True, 
                        help='Save extracted data to files')
    parser.add_argument('--skip-env-check', action='store_true',
                        help='Skip environment check')
    return parser.parse_args()

def main():
    """Main function to run the test script"""
    logger.info("\033[1;36m===== PDF Processing Pipeline Test =====\033[0m")
    
    args = parse_arguments()
    
    # Check environment
    if not args.skip_env_check:
        if not setup_environment():
            logger.error("\033[1;31mEnvironment check failed. Please fix the issues and try again.\033[0m")
            return 1
    
    # Import dependencies
    if not import_dependencies():
        logger.error("\033[1;31mDependency check failed. Please fix the issues and try again.\033[0m")
        return 1
    
    # Test direct Supabase insertion first as a sanity check
    if not test_direct_supabase_insert():
        logger.error("\033[1;31mDirect Supabase insertion test failed. Cannot continue with PDF processing.\033[0m")
        return 1
    
    # Find PDF files to test
    if args.pdf:
        pdf_files = [Path(args.pdf)] if os.path.exists(args.pdf) else []
    else:
        pdf_files = find_pdf_files(args.dir)
    
    if not pdf_files:
        logger.error("\033[1;31mNo PDF files found to test.\033[0m")
        return 1
    
    # Process each PDF
    success_count = 0
    for pdf_file in pdf_files:
        logger.info(f"\n\033[1;36m===== Testing {pdf_file.name} =====\033[0m")
        success = test_process_pdf(pdf_file, args.save)
        if success:
            success_count += 1
    
    # Print summary
    logger.info(f"\n\033[1;36m===== Test Summary =====\033[0m")
    logger.info(f"Processed {len(pdf_files)} PDF files")
    logger.info(f"Successfully processed: {success_count}")
    logger.info(f"Failed: {len(pdf_files) - success_count}")
    
    if success_count == len(pdf_files):
        logger.info("\033[1;32m✓ All PDF files were processed successfully!\033[0m")
        return 0
    else:
        logger.warning("\033[1;33mSome PDF files failed to process. Check the logs for details.\033[0m")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
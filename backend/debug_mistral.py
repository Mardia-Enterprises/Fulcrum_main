#!/usr/bin/env python3
"""
Debug script for Mistral API integration.
This script tests the connection to the Mistral API, checking available models
and PDF extraction capabilities.
"""

import os
import sys
import time
import json
from pathlib import Path
import requests
from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.exceptions import MistralAPIException, RateLimitError

# Setup paths
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent.parent
backend_dir = script_dir

# Load environment variables from root .env file
load_dotenv(root_dir / ".env")

def check_env_variables():
    """Check if required environment variables are set."""
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    
    if not mistral_api_key:
        print("\033[91mError: MISTRAL_API_KEY not found in .env file\033[0m")
        print("Please add your Mistral API key to the .env file in the root directory")
        print("Example: MISTRAL_API_KEY=your_api_key_here")
        return False
    
    print("\033[92m✓ MISTRAL_API_KEY found in environment variables\033[0m")
    # Only show first and last few characters of the key for security
    masked_key = mistral_api_key[:4] + "*" * (len(mistral_api_key) - 8) + mistral_api_key[-4:]
    print(f"API Key: {masked_key}")
    return True

def test_mistral_connection():
    """Test connection to Mistral API and list available models."""
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    
    try:
        client = MistralClient(api_key=mistral_api_key)
        print("\n\033[94mTesting Mistral API connection...\033[0m")
        
        retry_count = 0
        max_retries = 3
        backoff_time = 2  # Starting backoff time in seconds
        
        while retry_count < max_retries:
            try:
                models = client.list_models()
                print("\033[92m✓ Successfully connected to Mistral API\033[0m")
                print("\nAvailable models:")
                for model in models:
                    print(f"- {model.id}")
                return True
            except RateLimitError as e:
                retry_count += 1
                wait_time = backoff_time * (2 ** (retry_count - 1))  # Exponential backoff
                print(f"\033[93mRate limit hit. Retrying in {wait_time} seconds...\033[0m")
                time.sleep(wait_time)
                if retry_count == max_retries:
                    print("\033[91mError: Rate limit exceeded after multiple retries\033[0m")
                    print("Suggestions:")
                    print("1. Wait a few minutes before trying again")
                    print("2. Check your Mistral API usage in the dashboard")
                    print("3. Consider upgrading your Mistral API plan if hitting limits frequently")
                    return False
            except Exception as e:
                print(f"\033[91mError connecting to Mistral API: {str(e)}\033[0m")
                return False
    except Exception as e:
        print(f"\033[91mError initializing Mistral client: {str(e)}\033[0m")
        return False

def test_pdf_upload():
    """Test PDF upload and processing with Mistral API."""
    # Path to a sample PDF in the test_pdfs directory
    test_pdfs_dir = backend_dir / "resume_parser_f" / "test_pdfs"
    
    if not test_pdfs_dir.exists():
        print(f"\n\033[93mWarning: Test PDFs directory not found at {test_pdfs_dir}\033[0m")
        print("Creating test_pdfs directory...")
        test_pdfs_dir.mkdir(exist_ok=True)
        print("Please add sample PDFs to the test_pdfs directory and run this script again")
        return False
    
    pdf_files = list(test_pdfs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n\033[93mWarning: No PDF files found in {test_pdfs_dir}\033[0m")
        print("Please add sample PDFs to the test_pdfs directory and run this script again")
        return False
    
    # Use the first PDF file found
    sample_pdf = pdf_files[0]
    print(f"\n\033[94mTesting PDF processing with Mistral API using {sample_pdf.name}...\033[0m")
    
    try:
        # Direct API call for PDF processing to get detailed response
        url = "https://api.mistral.ai/v1/files/content"
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        headers = {
            "Authorization": f"Bearer {mistral_api_key}"
        }
        
        retry_count = 0
        max_retries = 3
        backoff_time = 2  # Starting backoff time in seconds
        
        while retry_count < max_retries:
            try:
                with open(sample_pdf, "rb") as file:
                    files = {"file": (sample_pdf.name, file, "application/pdf")}
                    response = requests.post(url, headers=headers, files=files)
                
                if response.status_code == 200:
                    print("\033[92m✓ Successfully processed PDF with Mistral API\033[0m")
                    
                    # Parse the response to a more readable format
                    content = response.json()
                    # Show just the first 200 characters to avoid cluttering the output
                    print(f"\nExtracted text (first 200 chars): \n{content.get('content', '')[:200]}...")
                    return True
                elif response.status_code == 429:
                    retry_count += 1
                    wait_time = backoff_time * (2 ** (retry_count - 1))  # Exponential backoff
                    print(f"\033[93mRate limit hit. Retrying in {wait_time} seconds...\033[0m")
                    time.sleep(wait_time)
                    if retry_count == max_retries:
                        print("\033[91mError: Rate limit exceeded after multiple retries\033[0m")
                        print("Suggestions:")
                        print("1. Wait a few minutes before trying again")
                        print("2. Check your Mistral API usage in the dashboard")
                        print("3. Consider implementing a queue system for processing multiple PDFs")
                        return False
                else:
                    print(f"\033[91mError processing PDF: {response.status_code}\033[0m")
                    try:
                        error_msg = response.json()
                        print(f"Error details: {json.dumps(error_msg, indent=2)}")
                    except:
                        print(f"Response text: {response.text}")
                    
                    print("\nTroubleshooting suggestions:")
                    print("1. Check if your PDF is valid and not corrupted")
                    print("2. Verify that your API key has the necessary permissions")
                    print("3. Check if the PDF file size is within Mistral's limits")
                    return False
            except Exception as e:
                print(f"\033[91mError during PDF processing: {str(e)}\033[0m")
                return False
    except Exception as e:
        print(f"\033[91mError setting up PDF processing: {str(e)}\033[0m")
        return False

def provide_troubleshooting_tips():
    """Provide troubleshooting tips for common issues."""
    print("\n\033[94mTroubleshooting Tips:\033[0m")
    print("1. API Key Issues:")
    print("   - Ensure your Mistral API key is correct and not expired")
    print("   - Make sure the API key is stored in the root .env file")
    
    print("\n2. Rate Limiting:")
    print("   - Mistral has rate limits on API calls")
    print("   - If processing multiple PDFs, implement a delay between requests")
    print("   - Consider using a queue system for batch processing")
    
    print("\n3. PDF Processing Issues:")
    print("   - Ensure PDFs are not corrupted or password-protected")
    print("   - Check if PDFs are within Mistral's file size limits")
    print("   - Try with a simpler, smaller PDF file for testing")
    
    print("\n4. Environment Setup:")
    print("   - Ensure all required packages are installed:")
    print("     pip install mistralai python-dotenv requests")
    print("   - Check if you have the latest version of the Mistral SDK")
    
    print("\n5. Network Issues:")
    print("   - Check your internet connection")
    print("   - If behind a proxy, ensure it's configured correctly")
    
    print("\n6. Data Structure:")
    print("   - If data extraction is working but not saving to Supabase,")
    print("   - Run the verify_uploads.py script to check database status")
    print("   - Check if the project data structure matches the expected format")

def main():
    """Main function to run all diagnostic tests."""
    print("\033[1m\n===== Mistral API Diagnostics =====\033[0m")
    
    # Check environment variables
    if not check_env_variables():
        provide_troubleshooting_tips()
        return 1
    
    # Test connection to Mistral API
    if not test_mistral_connection():
        provide_troubleshooting_tips()
        return 1
    
    # Test PDF upload and processing
    if not test_pdf_upload():
        provide_troubleshooting_tips()
        return 1
    
    print("\n\033[92m✓ All tests passed successfully!\033[0m")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
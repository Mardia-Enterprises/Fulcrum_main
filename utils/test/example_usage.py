#!/usr/bin/env python3
"""
Example script demonstrating how to use the S3Helper class.
This script shows common operations with AWS S3 storage.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path so we can import the S3Helper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cloud_helper import S3Helper

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_file(filepath, content="This is test content"):
    """Create a test file with some content."""
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath

def example_upload_single_file():
    """Example of uploading a single file to S3."""
    s3_helper = S3Helper()
    
    # Create a test file
    test_file = "test_upload.txt"
    create_test_file(test_file)
    
    try:
        # Upload the file
        success = s3_helper.s3_upload_file(
            local_file_path=test_file,
            key="example/test_upload.txt",
            metadata={"ContentType": "text/plain", "Description": "Test file"}
        )
        
        if success:
            logger.info(f"File {test_file} uploaded successfully")
        else:
            logger.error(f"Failed to upload {test_file}")
    finally:
        # Clean up the test file
        if os.path.exists(test_file):
            os.remove(test_file)

def example_upload_multiple_files():
    """Example of uploading multiple files to S3."""
    s3_helper = S3Helper()
    
    # Create test files
    files = []
    for i in range(3):
        filename = f"test_multi_{i}.txt"
        create_test_file(filename, f"This is test file {i}")
        files.append(filename)
    
    try:
        # Prepare file mappings
        file_mappings = [
            {
                'local_path': files[0],
                'key': f"example/multi/file1.txt",
                'metadata': {'ContentType': 'text/plain'}
            },
            {
                'local_path': files[1],
                'key': f"example/multi/file2.txt",
            },
            {
                'local_path': files[2],
                'key': f"example/multi/subfolder/file3.txt",
            }
        ]
        
        # Upload the files
        results = s3_helper.s3_upload_files(file_mappings)
        
        # Report results
        for file_path, success in results.items():
            if success:
                logger.info(f"File {file_path} uploaded successfully")
            else:
                logger.error(f"Failed to upload {file_path}")
    finally:
        # Clean up the test files
        for file in files:
            if os.path.exists(file):
                os.remove(file)

def example_list_objects():
    """Example of listing objects in S3 bucket."""
    s3_helper = S3Helper()
    
    # List all objects in the example folder
    objects = s3_helper.s3_list_objects(prefix="example/")
    
    if objects:
        logger.info(f"Found {len(objects)} objects:")
        for obj in objects:
            logger.info(f"  - {obj['Key']} ({obj.get('Size', 'unknown')} bytes)")
    else:
        logger.info("No objects found in the specified prefix")

def example_download_file():
    """Example of downloading a file from S3."""
    s3_helper = S3Helper()
    
    # Create a directory for downloads if it doesn't exist
    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    
    # Download a file
    key = "example/test_upload.txt"
    local_path = os.path.join(download_dir, "downloaded_file.txt")
    
    success = s3_helper.s3_download_file(key, local_path)
    
    if success:
        logger.info(f"File {key} downloaded successfully to {local_path}")
        # Display the content of the downloaded file
        with open(local_path, 'r') as f:
            content = f.read()
        logger.info(f"Content of the downloaded file: {content}")
    else:
        logger.error(f"Failed to download {key}")

def example_generate_presigned_url():
    """Example of generating a presigned URL for an S3 object."""
    s3_helper = S3Helper()
    
    # Generate a presigned URL
    key = "example/test_upload.txt"
    url = s3_helper.s3_generate_presigned_url(key, expiration=3600)  # 1 hour expiration
    
    if url:
        logger.info(f"Generated presigned URL for {key}:")
        logger.info(url)
    else:
        logger.error(f"Failed to generate presigned URL for {key}")

def example_copy_object():
    """Example of copying an object within S3."""
    s3_helper = S3Helper()
    
    # Copy an object
    source_key = "example/test_upload.txt"
    dest_key = "example/copy/test_upload_copy.txt"
    
    success = s3_helper.s3_copy_object(source_key, dest_key)
    
    if success:
        logger.info(f"Object {source_key} copied to {dest_key} successfully")
    else:
        logger.error(f"Failed to copy {source_key} to {dest_key}")

def example_delete_object():
    """Example of deleting an object from S3."""
    s3_helper = S3Helper()
    
    # Delete an object
    key = "example/copy/test_upload_copy.txt"
    
    success = s3_helper.s3_delete_object(key)
    
    if success:
        logger.info(f"Object {key} deleted successfully")
    else:
        logger.error(f"Failed to delete {key}")

def run_examples():
    """Run all the examples."""
    try:
        logger.info("Running S3Helper example usage")
        
        # Run examples
        example_upload_single_file()
        example_upload_multiple_files()
        example_list_objects()
        example_download_file()
        example_generate_presigned_url()
        example_copy_object()
        example_delete_object()
        
        logger.info("Examples completed successfully")
    except Exception as e:
        logger.exception(f"Error running examples: {e}")

if __name__ == "__main__":
    run_examples() 
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
from pathlib import Path

# Add parent directory to path so we can import the S3Helper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cloud_helper import S3Helper

class TestS3Helper(unittest.TestCase):
    """Test cases for S3Helper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'fake_access_key',
            'AWS_SECRET_ACCESS_KEY': 'fake_secret_key',
            'AWS_REGION': 'us-east-1',
            'S3_BUCKET_NAME': 'test-bucket',
            'S3_FOLDER_PATH': 'test-folder'
        })
        self.env_patcher.start()
        
        # Create mock S3 client and resource
        self.s3_client_patcher = patch('boto3.client')
        self.s3_resource_patcher = patch('boto3.resource')
        
        self.mock_s3_client = self.s3_client_patcher.start()
        self.mock_s3_resource = self.s3_resource_patcher.start()
        
        # Mock S3 client instance
        self.mock_client_instance = MagicMock()
        self.mock_s3_client.return_value = self.mock_client_instance
        
        # Mock S3 resource instance and bucket
        self.mock_resource_instance = MagicMock()
        self.mock_bucket = MagicMock()
        self.mock_resource_instance.Bucket.return_value = self.mock_bucket
        self.mock_s3_resource.return_value = self.mock_resource_instance
        
        # Create S3Helper instance
        self.s3_helper = S3Helper()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.s3_client_patcher.stop()
        self.s3_resource_patcher.stop()
    
    def test_init(self):
        """Test initialization of S3Helper."""
        self.assertEqual(self.s3_helper.aws_access_key, 'fake_access_key')
        self.assertEqual(self.s3_helper.aws_secret_key, 'fake_secret_key')
        self.assertEqual(self.s3_helper.region, 'us-east-1')
        self.assertEqual(self.s3_helper.bucket_name, 'test-bucket')
        self.assertEqual(self.s3_helper.folder_path, 'test-folder')
        
        # Verify client and resource were created with correct parameters
        self.mock_s3_client.assert_called_with(
            's3',
            aws_access_key_id='fake_access_key',
            aws_secret_access_key='fake_secret_key',
            region_name='us-east-1'
        )
        
        self.mock_s3_resource.assert_called_with(
            's3',
            aws_access_key_id='fake_access_key',
            aws_secret_access_key='fake_secret_key',
            region_name='us-east-1'
        )
    
    def test_get_full_s3_key(self):
        """Test _get_full_s3_key method."""
        # Test with folder path and regular key
        full_key = self.s3_helper._get_full_s3_key('test-file.txt')
        self.assertEqual(full_key, 'test-folder/test-file.txt')
        
        # Test with trailing slash in folder path
        self.s3_helper.folder_path = 'test-folder/'
        full_key = self.s3_helper._get_full_s3_key('test-file.txt')
        self.assertEqual(full_key, 'test-folder/test-file.txt')
        
        # Test with leading slash in key
        full_key = self.s3_helper._get_full_s3_key('/test-file.txt')
        self.assertEqual(full_key, 'test-folder/test-file.txt')
        
        # Test with empty folder path
        self.s3_helper.folder_path = ''
        full_key = self.s3_helper._get_full_s3_key('test-file.txt')
        self.assertEqual(full_key, 'test-file.txt')
    
    def test_s3_upload_file(self):
        """Test s3_upload_file method."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_file_path = temp_file.name
        
        try:
            # Test successful upload
            self.s3_helper.folder_path = 'test-folder'
            result = self.s3_helper.s3_upload_file(temp_file_path, 'test-upload.txt')
            
            # Check that the file was uploaded with the correct parameters
            self.mock_client_instance.upload_file.assert_called_with(
                temp_file_path,
                'test-bucket',
                'test-folder/test-upload.txt',
                ExtraArgs={}
            )
            self.assertTrue(result)
            
            # Test upload with metadata
            metadata = {'ContentType': 'text/plain'}
            self.s3_helper.s3_upload_file(
                temp_file_path, 
                'test-metadata.txt',
                metadata=metadata
            )
            
            self.mock_client_instance.upload_file.assert_called_with(
                temp_file_path,
                'test-bucket',
                'test-folder/test-metadata.txt',
                ExtraArgs={'Metadata': metadata}
            )
            
            # Test upload failure
            self.mock_client_instance.upload_file.side_effect = Exception("Upload failed")
            result = self.s3_helper.s3_upload_file(temp_file_path, 'test-fail.txt')
            self.assertFalse(result)
            
            # Reset mock
            self.mock_client_instance.upload_file.side_effect = None
            
            # Test non-existent file
            result = self.s3_helper.s3_upload_file('non-existent-file.txt')
            self.assertFalse(result)
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def test_s3_download_file(self):
        """Test s3_download_file method."""
        # Set up temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = os.path.join(temp_dir, 'test-download.txt')
            
            # Test successful download
            self.s3_helper.folder_path = 'test-folder'
            result = self.s3_helper.s3_download_file('test-file.txt', download_path)
            
            # Check that the file was downloaded with the correct parameters
            self.mock_client_instance.download_file.assert_called_with(
                'test-bucket',
                'test-folder/test-file.txt',
                download_path
            )
            self.assertTrue(result)
            
            # Test download failure - 404
            error_response = {'Error': {'Code': '404'}}
            self.mock_client_instance.download_file.side_effect = Exception("Download failed")
            self.mock_client_instance.download_file.side_effect.__class__ = type('ClientError', (Exception,), {})
            self.mock_client_instance.download_file.side_effect.response = error_response
            
            result = self.s3_helper.s3_download_file('missing-file.txt', download_path)
            self.assertFalse(result)
    
    def test_s3_list_objects(self):
        """Test s3_list_objects method."""
        # Mock list_objects_v2 response
        mock_response = {
            'Contents': [
                {'Key': 'test-folder/file1.txt', 'Size': 100, 'LastModified': '2023-01-01'},
                {'Key': 'test-folder/file2.txt', 'Size': 200, 'LastModified': '2023-01-02'}
            ]
        }
        self.mock_client_instance.list_objects_v2.return_value = mock_response
        
        # Test list objects
        self.s3_helper.folder_path = 'test-folder'
        result = self.s3_helper.s3_list_objects()
        
        # Check that list_objects_v2 was called with the correct parameters
        self.mock_client_instance.list_objects_v2.assert_called_with(
            Bucket='test-bucket',
            Prefix='test-folder',
            MaxKeys=1000
        )
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['Key'], 'test-folder/file1.txt')
        self.assertEqual(result[1]['Key'], 'test-folder/file2.txt')
        
        # Test with prefix
        result = self.s3_helper.s3_list_objects('subfolder')
        self.mock_client_instance.list_objects_v2.assert_called_with(
            Bucket='test-bucket',
            Prefix='test-folder/subfolder',
            MaxKeys=1000
        )
        
        # Test error case
        self.mock_client_instance.list_objects_v2.side_effect = Exception("List failed")
        result = self.s3_helper.s3_list_objects()
        self.assertEqual(result, [])
    
    def test_s3_delete_object(self):
        """Test s3_delete_object method."""
        # Test successful delete
        self.s3_helper.folder_path = 'test-folder'
        result = self.s3_helper.s3_delete_object('test-file.txt')
        
        # Check that delete_object was called with the correct parameters
        self.mock_client_instance.delete_object.assert_called_with(
            Bucket='test-bucket',
            Key='test-folder/test-file.txt'
        )
        self.assertTrue(result)
        
        # Test delete failure
        self.mock_client_instance.delete_object.side_effect = Exception("Delete failed")
        result = self.s3_helper.s3_delete_object('test-file.txt')
        self.assertFalse(result)
    
    def test_s3_check_object_exists(self):
        """Test s3_check_object_exists method."""
        # Test object exists
        self.s3_helper.folder_path = 'test-folder'
        result = self.s3_helper.s3_check_object_exists('test-file.txt')
        
        # Check that head_object was called with the correct parameters
        self.mock_client_instance.head_object.assert_called_with(
            Bucket='test-bucket',
            Key='test-folder/test-file.txt'
        )
        self.assertTrue(result)
        
        # Test object doesn't exist
        error_response = {'Error': {'Code': '404'}}
        self.mock_client_instance.head_object.side_effect = Exception("Not found")
        self.mock_client_instance.head_object.side_effect.__class__ = type('ClientError', (Exception,), {})
        self.mock_client_instance.head_object.side_effect.response = error_response
        
        result = self.s3_helper.s3_check_object_exists('missing-file.txt')
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 
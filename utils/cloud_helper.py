import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class S3Helper:
    """
    Helper class for AWS S3 operations.
    Uses credentials from environment variables.
    """
    
    def __init__(self):
        """Initialize S3 client and resources using environment variables."""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.folder_path = os.getenv('S3_FOLDER_PATH', '')
        
        if not all([self.aws_access_key, self.aws_secret_key, self.region, self.bucket_name]):
            raise ValueError("AWS credentials or bucket not properly configured in .env file")
        
        # Initialize the S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        
        # Initialize S3 resource for higher-level operations
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        
        # Get the bucket
        self.bucket = self.s3_resource.Bucket(self.bucket_name)
    
    def _get_full_s3_key(self, key: str) -> str:
        """
        Constructs the full S3 key by combining the folder path and key.
        
        Args:
            key: The object key without the folder prefix
        
        Returns:
            The complete S3 key with folder prefix
        """
        if not self.folder_path:
            return key
        
        # Remove any leading/trailing slashes and combine
        folder = self.folder_path.strip('/')
        key = key.strip('/')
        
        if not folder:
            return key
        
        return f"{folder}/{key}"
    
    def s3_upload_file(self, local_file_path: str, key: Optional[str] = None, 
                   metadata: Optional[Dict[str, str]] = None, 
                   extra_args: Optional[Dict[str, Any]] = None) -> bool:
        """
        Upload a file to an S3 bucket.
        
        Args:
            local_file_path: Path to the local file
            key: S3 object key (if None, uses the filename)
            metadata: Optional metadata dictionary
            extra_args: Optional extra arguments for upload
            
        Returns:
            True if file was uploaded successfully, else False
        """
        if not os.path.exists(local_file_path):
            logger.error(f"File {local_file_path} does not exist")
            return False
        
        # If key is not provided, use the filename
        if key is None:
            key = os.path.basename(local_file_path)
        
        # Construct the full S3 key with folder path
        full_key = self._get_full_s3_key(key)
        
        # Prepare upload parameters
        upload_args = {}
        if metadata:
            upload_args['Metadata'] = metadata
        if extra_args:
            upload_args.update(extra_args)
        
        try:
            logger.info(f"Uploading {local_file_path} to {self.bucket_name}/{full_key}")
            self.s3_client.upload_file(
                local_file_path, 
                self.bucket_name, 
                full_key,
                ExtraArgs=upload_args
            )
            logger.info(f"Successfully uploaded {local_file_path} to {self.bucket_name}/{full_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return False
    
    def s3_upload_files(self, file_mappings: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Upload multiple files to S3 bucket.
        
        Args:
            file_mappings: List of dictionaries with file info
                Each dict should contain:
                - 'local_path': Required local file path
                - 'key': Optional S3 key (if None, uses filename)
                - 'metadata': Optional metadata dict
                - 'extra_args': Optional extra args for upload
                
        Returns:
            Dictionary mapping filenames to success status
        """
        results = {}
        
        for file_info in file_mappings:
            local_path = file_info.get('local_path')
            if not local_path:
                logger.error("Missing local_path in file mapping")
                continue
                
            key = file_info.get('key', os.path.basename(local_path))
            metadata = file_info.get('metadata')
            extra_args = file_info.get('extra_args')
            
            success = self.s3_upload_file(
                local_path, 
                key=key,
                metadata=metadata,
                extra_args=extra_args
            )
            
            results[local_path] = success
            
        return results
    
    def s3_download_file(self, key: str, local_file_path: str) -> bool:
        """
        Download a file from S3 bucket.
        
        Args:
            key: S3 object key
            local_file_path: Path where to save the file locally
            
        Returns:
            True if file was downloaded successfully, else False
        """
        # Construct the full S3 key
        full_key = self._get_full_s3_key(key)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True)
            
            logger.info(f"Downloading {self.bucket_name}/{full_key} to {local_file_path}")
            self.s3_client.download_file(
                self.bucket_name,
                full_key,
                local_file_path
            )
            logger.info(f"Successfully downloaded {self.bucket_name}/{full_key} to {local_file_path}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"The object {full_key} does not exist in bucket {self.bucket_name}")
            else:
                logger.error(f"Error downloading file from S3: {e}")
            return False
    
    def s3_download_files(self, mappings: List[Dict[str, str]]) -> Dict[str, bool]:
        """
        Download multiple files from S3 bucket.
        
        Args:
            mappings: List of dictionaries with keys:
                - 'key': S3 object key
                - 'local_path': Local destination path
                
        Returns:
            Dictionary mapping keys to success status
        """
        results = {}
        
        for mapping in mappings:
            key = mapping.get('key')
            local_path = mapping.get('local_path')
            
            if not key or not local_path:
                logger.error("Missing key or local_path in mapping")
                continue
                
            success = self.s3_download_file(key, local_path)
            results[key] = success
            
        return results
    
    def s3_list_objects(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in the S3 bucket with optional prefix.
        
        Args:
            prefix: Prefix to filter objects (will be combined with folder_path)
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object dictionaries with keys like 'Key', 'LastModified', 'Size', etc.
        """
        # Combine folder path with prefix if both exist
        if self.folder_path and prefix:
            full_prefix = f"{self.folder_path.strip('/')}/{prefix.strip('/')}"
        elif self.folder_path:
            full_prefix = self.folder_path
        else:
            full_prefix = prefix
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=full_prefix,
                MaxKeys=max_keys
            )
            
            objects = response.get('Contents', [])
            return objects
        except ClientError as e:
            logger.error(f"Error listing objects in S3: {e}")
            return []
    
    def s3_delete_object(self, key: str) -> bool:
        """
        Delete an object from S3 bucket.
        
        Args:
            key: S3 object key to delete
            
        Returns:
            True if object was deleted successfully, else False
        """
        # Construct the full S3 key
        full_key = self._get_full_s3_key(key)
        
        try:
            logger.info(f"Deleting {self.bucket_name}/{full_key}")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            logger.info(f"Successfully deleted {self.bucket_name}/{full_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object from S3: {e}")
            return False
    
    def s3_delete_objects(self, keys: List[str]) -> Dict[str, bool]:
        """
        Delete multiple objects from S3 bucket.
        
        Args:
            keys: List of S3 object keys to delete
            
        Returns:
            Dictionary mapping keys to success status
        """
        if not keys:
            return {}
            
        # Prepare delete objects format
        objects = [{'Key': self._get_full_s3_key(key)} for key in keys]
        
        try:
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={
                    'Objects': objects
                }
            )
            
            # Check which objects were successfully deleted
            deleted = {obj['Key'] for obj in response.get('Deleted', [])}
            errors = {err['Key']: err['Message'] for err in response.get('Errors', [])}
            
            results = {}
            for key in keys:
                full_key = self._get_full_s3_key(key)
                results[key] = full_key in deleted
                if full_key in errors:
                    logger.error(f"Error deleting {full_key}: {errors[full_key]}")
            
            return results
        except ClientError as e:
            logger.error(f"Error batch deleting objects from S3: {e}")
            return {key: False for key in keys}
    
    def s3_check_object_exists(self, key: str) -> bool:
        """
        Check if an object exists in the S3 bucket.
        
        Args:
            key: S3 object key
            
        Returns:
            True if object exists, else False
        """
        # Construct the full S3 key
        full_key = self._get_full_s3_key(key)
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking if object exists in S3: {e}")
                return False
    
    def s3_get_object_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for an S3 object.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary of object metadata or empty dict if error
        """
        # Construct the full S3 key
        full_key = self._get_full_s3_key(key)
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=full_key
            )
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"Object {full_key} does not exist")
            else:
                logger.error(f"Error getting object metadata from S3: {e}")
            return {}
    
    def s3_generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for an S3 object.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if error
        """
        # Construct the full S3 key
        full_key = self._get_full_s3_key(key)
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': full_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def s3_copy_object(self, source_key: str, dest_key: str) -> bool:
        """
        Copy an object within the S3 bucket.
        
        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key
            
        Returns:
            True if object was copied successfully, else False
        """
        # Construct the full S3 keys
        full_source_key = self._get_full_s3_key(source_key)
        full_dest_key = self._get_full_s3_key(dest_key)
        
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={
                    'Bucket': self.bucket_name,
                    'Key': full_source_key
                },
                Key=full_dest_key
            )
            logger.info(f"Successfully copied {full_source_key} to {full_dest_key}")
            return True
        except ClientError as e:
            logger.error(f"Error copying object in S3: {e}")
            return False 
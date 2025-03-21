#!/usr/bin/env python3
"""
Compatibility layer for Mistral API versions.
This module provides a unified interface for working with both old (0.4.2) and newer Mistral API versions.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - \033[1;33m%(levelname)s\033[0m - %(message)s',
    handlers=[
        logging.FileHandler("resume_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define our own exception classes
class MistralAPIError(Exception):
    """Base exception for Mistral API errors."""
    pass

class RateLimitError(MistralAPIError):
    """Exception for rate limit errors."""
    pass

class FileMock:
    """Mock for the file upload response in newer Mistral API versions"""
    def __init__(self, file_url: str):
        self.file_url = file_url

class MistralClientCompat:
    """Compatibility wrapper for MistralClient"""
    
    def __init__(self, api_key: str):
        """Initialize the client with the API key"""
        self.api_key = api_key
        self.client = None
        self.is_legacy = False
        
        # Import the Mistral client
        try:
            from mistralai.client import MistralClient
            
            # Initialize the client
            self.client = MistralClient(api_key=api_key)
            
            # Import exception classes if available
            try:
                import mistralai.exceptions
                if hasattr(mistralai.exceptions, 'MistralAPIError'):
                    self.MistralAPIError = mistralai.exceptions.MistralAPIError
                else:
                    # Use our own exception class
                    self.MistralAPIError = MistralAPIError
                    
                if hasattr(mistralai.exceptions, 'RateLimitError'):
                    self.RateLimitError = mistralai.exceptions.RateLimitError
                else:
                    # Use our own exception class
                    self.RateLimitError = RateLimitError
            except ImportError:
                # Use our own exception classes
                self.MistralAPIError = MistralAPIError
                self.RateLimitError = RateLimitError
                
            # Check if we're using a legacy version
            if not hasattr(self.client, 'upload_file'):
                self.is_legacy = True
                logger.warning("\033[93mUsing legacy Mistral API (v0.4.2), file upload not supported\033[0m")
            else:
                logger.info("\033[92m✓ Using modern Mistral API with file upload support\033[0m")
                
        except ImportError:
            logger.error("\033[91mError: Failed to import Mistral AI client\033[0m")
            raise
        except Exception as e:
            logger.error(f"\033[91mError initializing Mistral client: {str(e)}\033[0m")
            raise
    
    def upload_file(self, file: BinaryIO, file_name: str) -> FileMock:
        """
        Upload a file to Mistral AI.
        In legacy mode (v0.4.2), this extracts the text and returns a mock file URL.
        
        Args:
            file: File object
            file_name: Name of the file
            
        Returns:
            FileMock with a file_url attribute
        """
        if not self.is_legacy and hasattr(self.client, 'upload_file'):
            # Use the native upload_file method if available
            return self.client.upload_file(file=file, file_name=file_name)
        
        # Legacy mode: extract text and create a fake file URL
        logger.info("\033[93mLegacy mode: Extracting text from file instead of uploading\033[0m")
        
        # Check if it's a PDF
        if file_name.lower().endswith('.pdf'):
            try:
                import pdfplumber
                
                # Create a temporary file to store the PDF content
                temp_path = Path(f"./temp_{file_name}")
                with open(temp_path, 'wb') as temp_file:
                    temp_file.write(file.read())
                
                # Extract text from the PDF
                text_content = ""
                with pdfplumber.open(temp_path) as pdf:
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""
                
                # Clean up the temporary file
                if temp_path.exists():
                    temp_path.unlink()
                
                # Create a unique file ID
                import hashlib
                file_id = hashlib.md5(text_content.encode()).hexdigest()
                
                # Save the extracted text to a JSON file
                output_dir = Path("./debug")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"{file_name.replace('.pdf', '')}_extracted.json"
                
                with open(output_path, 'w') as f:
                    json.dump({"content": text_content}, f, indent=2)
                
                # Return a mock file URL that includes the file ID
                return FileMock(file_url=f"file://{output_path}")
                
            except ImportError:
                logger.error("\033[91mError: pdfplumber not installed, cannot extract text from PDF\033[0m")
                raise
            except Exception as e:
                logger.error(f"\033[91mError extracting text from PDF: {str(e)}\033[0m")
                raise
        else:
            # For non-PDF files, just read the content
            content = file.read()
            file_id = hash(content)
            return FileMock(file_url=f"file://local/{file_id}/{file_name}")
    
    def chat(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 1024, **kwargs) -> Any:
        """Proxy for the chat method"""
        return self.client.chat(model=model, messages=messages, max_tokens=max_tokens, **kwargs)
    
    def embeddings(self, model: str, input: Union[str, List[str]], **kwargs) -> Any:
        """Proxy for the embeddings method"""
        return self.client.embeddings(model=model, input=input, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Proxy for any other methods"""
        if hasattr(self.client, name):
            return getattr(self.client, name)
        raise AttributeError(f"'MistralClientCompat' object has no attribute '{name}'")


def get_mistral_client(api_key: str) -> MistralClientCompat:
    """Get a compatible Mistral client"""
    return MistralClientCompat(api_key=api_key) 
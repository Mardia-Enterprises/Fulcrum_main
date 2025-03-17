"""
PDF Processor using Mistral OCR.
This module handles the extraction of text from PDF files using Mistral AI's OCR capabilities.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MistralPDFProcessor:
    """Process PDF files using Mistral AI's OCR capabilities."""
    
    def __init__(self):
        """Initialize the Mistral PDF processor."""
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables.")
        
        self.api_url = "https://api.mistral.ai/v1/documents/inputs"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text from a PDF file using Mistral OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing the extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return {"error": f"File not found: {pdf_path}"}
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Open PDF file
            with open(pdf_path, "rb") as pdf_file:
                files = {"file": (os.path.basename(pdf_path), pdf_file, "application/pdf")}
                
                # Make API request to Mistral
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files
                )
                
                # Check if request was successful
                if response.status_code != 200:
                    logger.error(f"Error extracting text from PDF. Status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return {"error": f"API Error: {response.text}"}
                
                # Get document ID from response
                doc_data = response.json()
                doc_id = doc_data.get("id")
                
                # Retrieve the processed content
                content = self._retrieve_processed_content(doc_id)
                
                # Add metadata
                result = {
                    "document_id": doc_id,
                    "filename": os.path.basename(pdf_path),
                    "content": content,
                    "file_path": pdf_path,
                }
                
                return result
        
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return {"error": str(e)}
    
    def _retrieve_processed_content(self, doc_id: str) -> Dict:
        """
        Retrieve the processed content from Mistral API.
        
        Args:
            doc_id: Document ID returned by the API
            
        Returns:
            Dict containing the processed content
        """
        retrieval_url = f"https://api.mistral.ai/v1/documents/outputs/{doc_id}"
        
        try:
            # Poll until processing is complete
            while True:
                response = requests.get(
                    retrieval_url,
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error retrieving document. Status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return {"error": f"API Error: {response.text}"}
                
                data = response.json()
                status = data.get("status")
                
                if status == "ready":
                    # Document is processed
                    return data
                elif status == "failed":
                    logger.error(f"Document processing failed: {data.get('error')}")
                    return {"error": data.get("error")}
                else:
                    # Wait a bit before polling again
                    import time
                    time.sleep(2)
        
        except Exception as e:
            logger.error(f"Error retrieving document content: {str(e)}")
            return {"error": str(e)}
    
    def process_pdf_directory(self, directory_path: str) -> List[Dict]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDF files
            
        Returns:
            List of dictionaries with extracted text and metadata
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        results = []
        for file in os.listdir(directory_path):
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(directory_path, file)
                result = self.extract_text_from_pdf(pdf_path)
                if "error" not in result:
                    results.append(result)
                    logger.info(f"Successfully processed PDF: {file}")
                else:
                    logger.error(f"Failed to process PDF {file}: {result['error']}")
        
        logger.info(f"Processed {len(results)} PDF files from {directory_path}")
        return results


def main():
    """Test the PDF processor with a sample PDF file."""
    pdf_dir = "pdf_data/raw-files"
    processor = MistralPDFProcessor()
    results = processor.process_pdf_directory(pdf_dir)
    
    # Print extracted text from first PDF for testing
    if results:
        first_result = results[0]
        print(f"File: {first_result['filename']}")
        print(f"Document ID: {first_result['document_id']}")
        print(f"Content sample: {first_result['content']['content'][:500]}...")


if __name__ == "__main__":
    main() 
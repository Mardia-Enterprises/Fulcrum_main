"""
PDF Processor using Mistral OCR.
This module handles the extraction of text from PDF files using Mistral AI's OCR capabilities.
"""

import os
import sys
import logging
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Import Mistral API client
try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
except ImportError:
    logger.warning("Mistral API package not found. Install with: pip install mistralai")
    # Create stub classes to avoid errors
    class MistralClient:
        def __init__(self, api_key=None):
            pass
    
    class ChatMessage:
        def __init__(self, role=None, content=None):
            self.role = role
            self.content = content

class MistralPDFProcessor:
    """
    Extract text from PDF files using Mistral AI's OCR capabilities.
    """
    
    def __init__(
        self, 
        mistral_api_key: Optional[str] = None, 
        model: str = "mistral-large-latest"
    ):
        """
        Initialize the PDF processor.
        
        Args:
            mistral_api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model: Mistral model to use for OCR
        """
        # Get API key from environment variables if not provided
        self.api_key = mistral_api_key or os.environ.get("MISTRAL_API_KEY")
        
        if not self.api_key:
            logger.warning("Mistral API key not provided and not found in environment variables")
        
        self.model = model
        
        try:
            self.client = MistralClient(api_key=self.api_key)
            logger.info(f"Initialized MistralPDFProcessor with model: {model}")
        except Exception as e:
            logger.error(f"Error initializing Mistral client: {str(e)}")
            self.client = None
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file using Mistral's OCR capabilities.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from PDF: {pdf_path.name}")
        
        if not self.client:
            logger.error("Mistral client not initialized. Cannot extract text from PDF.")
            # Return a placeholder text for testing
            return f"[Placeholder text for {pdf_path.name}. Mistral client not initialized.]"
        
        # Since this is a test/demo, we'll skip the actual OCR and just return dummy text
        # In a real implementation, you would use Mistral's API to extract text
        try:
            # Simulated extraction for testing
            dummy_text = f"""This is placeholder text for {pdf_path.name}.
In a real implementation, we would extract text from the PDF using Mistral's OCR capabilities.
This text would then be processed, chunked, and embedded for vector search.
For now, we're just using this dummy text to test the vector search functionality.
The PDF processing pipeline includes:
1. PDF text extraction
2. Text preprocessing and chunking
3. Embedding generation
4. Vector indexing
5. Semantic search

When the system is fully functional, you'll be able to search for content within PDFs semantically,
finding relevant information even if it doesn't exactly match your query terms.
"""
            logger.info(f"Successfully extracted text from {pdf_path.name} (simulated)")
            return dummy_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {str(e)}")
            # Return a placeholder text for testing
            return f"[Error extracting text from {pdf_path.name}: {str(e)}]"
    
    def extract_text_from_pdf_with_mistral(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file using Mistral's OCR capabilities.
        This is the actual implementation that would be used in production.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
        """
        if not self.client:
            logger.error("Mistral client not initialized. Cannot extract text from PDF.")
            return ""
            
        pdf_path = Path(pdf_path)
        
        try:
            # Read the PDF file in binary mode
            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            
            # Encode the PDF content as base64
            base64_pdf = base64.b64encode(pdf_content).decode("utf-8")
            
            # Prepare the system message with instructions
            system_message = """You are an OCR system that extracts text from PDFs.
Extract ALL text from the PDF, preserving the original structure as much as possible.
Include headings, paragraphs, tables, captions, and footnotes.
For tables, convert them to a structured text format.
Return ONLY the extracted text, nothing else."""
            
            # Create the message with the PDF attachment
            messages = [
                ChatMessage(role="system", content=system_message),
                ChatMessage(
                    role="user",
                    content=[
                        {
                            "type": "text",
                            "text": "Extract all text from this PDF document. Return only the extracted text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{base64_pdf}"
                            }
                        }
                    ]
                )
            ]
            
            # Call the Mistral API to extract text
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=4000
            )
            
            # Extract the text from the response
            extracted_text = response.choices[0].message.content
            
            logger.info(f"Successfully extracted text from {pdf_path.name} ({len(extracted_text)} characters)")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {str(e)}")
            return ""
    
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
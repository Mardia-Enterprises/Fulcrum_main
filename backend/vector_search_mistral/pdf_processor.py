"""
PDF Processor for Vector Search
-------------------------------------------------------------------------------
This module extracts and processes text from PDF files for use in vector search.
It provides robust functionality for converting PDF documents into processable
text, handling various PDF formats, structures, and potential extraction issues.

In production environments, this module ensures reliable text extraction with
appropriate error handling and logging. It processes PDFs efficiently while
maintaining document context and metadata association.

Key features:
- Production-ready PDF text extraction
- Metadata extraction and preservation
- Robust error handling for corrupted or complex PDFs
- Batch processing capabilities
- Support for various PDF formats and structures
"""

import os
import logging
import sys
import io
import re
import hashlib
import time
from typing import List, Dict, Any, Union, Optional, Tuple, BinaryIO
from pathlib import Path
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("pdf_processor")

# Import PDF libraries with error handling
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    logger.warning("PyPDF2 package not found. Install with: pip install PyPDF2>=3.0.0")
    PYPDF2_AVAILABLE = False
    PyPDF2 = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    logger.warning("pdfminer.six package not found. Install with: pip install pdfminer.six>=20221105")
    PDFMINER_AVAILABLE = False
    pdfminer_extract_text = None

# Import local modules
from .text_preprocessor import TextPreprocessor, create_text_preprocessor

class PDFProcessor:
    """
    Process PDF files for text extraction and preparation for embeddings.
    
    This class handles the extraction of text from PDF files, along with
    preprocessing for embedding generation, maintaining document context
    and metadata association.
    """
    
    def __init__(
        self,
        preprocessor: Optional[TextPreprocessor] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_fallback: bool = True
    ):
        """
        Initialize the PDF processor.
        
        Args:
            preprocessor: Text preprocessor instance (created if not provided)
            chunk_size: Maximum chunk size for text preprocessing
            chunk_overlap: Chunk overlap for text preprocessing
            use_fallback: Whether to use fallback extraction methods
        """
        # Initialize text preprocessor if not provided
        self.preprocessor = preprocessor or create_text_preprocessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.use_fallback = use_fallback
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Determine available PDF extraction methods
        self.extraction_methods = []
        
        if PYPDF2_AVAILABLE:
            self.extraction_methods.append("pypdf2")
        
        if PDFMINER_AVAILABLE:
            self.extraction_methods.append("pdfminer")
        
        if not self.extraction_methods:
            logger.error("No PDF extraction libraries available. Install PyPDF2 or pdfminer.six.")
        else:
            logger.info(f"PDF processor initialized with extraction methods: {', '.join(self.extraction_methods)}")
    
    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF file for embedding generation.
        
        This method extracts text from a PDF file, preprocesses it, and
        prepares it for embedding generation.
        
        Args:
            pdf_path: Path to the PDF file
            metadata: Additional metadata to include
            
        Returns:
            Dictionary with extracted text, chunks, and metadata
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a PDF
        """
        # Convert to Path object if string
        pdf_path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
        
        # Check if file exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Check if file is a PDF
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        # Get file metadata
        file_metadata = self._get_file_metadata(pdf_path)
        
        # Combine with provided metadata
        combined_metadata = {
            **(metadata or {}),
            **file_metadata
        }
        
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        try:
            # Extract text from PDF
            extracted_text = self._extract_text(pdf_path)
            
            if not extracted_text:
                logger.warning(f"No text extracted from PDF: {pdf_path.name}")
                return {
                    "id": combined_metadata.get("file_id", str(uuid.uuid4())),
                    "filename": pdf_path.name,
                    "text": "",
                    "chunks": [],
                    "metadata": combined_metadata,
                    "error": "No text extracted from PDF"
                }
            
            # Preprocess extracted text
            processed_result = self.preprocessor.process_text(extracted_text, combined_metadata)
            
            # Add document ID if not present
            if "id" not in processed_result:
                processed_result["id"] = combined_metadata.get("file_id", str(uuid.uuid4()))
            
            # Add filename if not present
            if "filename" not in processed_result:
                processed_result["filename"] = pdf_path.name
            
            logger.info(f"Processed PDF into {len(processed_result['chunks'])} chunks: {pdf_path.name}")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path.name}: {str(e)}")
            return {
                "id": combined_metadata.get("file_id", str(uuid.uuid4())),
                "filename": pdf_path.name,
                "text": "",
                "chunks": [],
                "metadata": combined_metadata,
                "error": str(e)
            }
    
    def process_pdf_batch(
        self,
        pdf_paths: List[Union[str, Path]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files in batch mode.
        
        Args:
            pdf_paths: List of paths to PDF files
            metadata: Common metadata to include for all files
            
        Returns:
            List of processed PDF results
        """
        results = []
        
        for pdf_path in pdf_paths:
            try:
                # Process individual PDF
                result = self.process_pdf(pdf_path, metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch processing for {pdf_path}: {str(e)}")
                # Add error entry
                file_name = Path(pdf_path).name if isinstance(pdf_path, str) else pdf_path.name
                results.append({
                    "id": str(uuid.uuid4()),
                    "filename": file_name,
                    "text": "",
                    "chunks": [],
                    "metadata": {
                        **(metadata or {}),
                        "filename": file_name,
                        "error": str(e)
                    },
                    "error": str(e)
                })
        
        logger.info(f"Batch processed {len(results)} PDF files ({len([r for r in results if 'error' not in r])} successful)")
        return results
    
    def process_dir(
        self,
        directory: Union[str, Path],
        recursive: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process all PDF files in a directory.
        
        Args:
            directory: Directory containing PDF files
            recursive: Whether to search subdirectories
            metadata: Common metadata to include for all files
            
        Returns:
            List of processed PDF results
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
        """
        # Convert to Path object if string
        directory = Path(directory) if isinstance(directory, str) else directory
        
        # Check if directory exists
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Get all PDF files in directory
        if recursive:
            pdf_paths = list(directory.glob('**/*.pdf'))
        else:
            pdf_paths = list(directory.glob('*.pdf'))
        
        logger.info(f"Found {len(pdf_paths)} PDF files in directory: {directory}")
        
        # Process PDFs in batch
        return self.process_pdf_batch(pdf_paths, metadata)
    
    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file using available extraction methods.
        
        This method tries multiple extraction methods in order of preference
        to ensure the best possible text extraction.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
            
        Raises:
            RuntimeError: If no extraction methods are available
        """
        if not self.extraction_methods:
            raise RuntimeError("No PDF extraction libraries available")
        
        # Try extraction methods in order
        extracted_text = ""
        extraction_errors = []
        
        for method in self.extraction_methods:
            try:
                if method == "pypdf2":
                    extracted_text = self._extract_with_pypdf2(pdf_path)
                elif method == "pdfminer":
                    extracted_text = self._extract_with_pdfminer(pdf_path)
                
                # If we got text and it's not just whitespace, return it
                if extracted_text and extracted_text.strip():
                    logger.info(f"Successfully extracted text using {method}: {pdf_path.name}")
                    return extracted_text
                
            except Exception as e:
                logger.warning(f"Error extracting text with {method}: {str(e)}")
                extraction_errors.append(f"{method}: {str(e)}")
        
        # If we got here, all methods failed
        logger.error(f"All extraction methods failed for {pdf_path.name}: {'; '.join(extraction_errors)}")
        return ""
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF using PyPDF2.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text
            
        Raises:
            ImportError: If PyPDF2 is not available
            Exception: For any extraction errors
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 library not available")
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                return "\n\n".join(text_parts)
                
        except Exception as e:
            logger.error(f"PyPDF2 extraction error for {pdf_path.name}: {str(e)}")
            raise
    
    def _extract_with_pdfminer(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF using pdfminer.six.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text
            
        Raises:
            ImportError: If pdfminer.six is not available
            Exception: For any extraction errors
        """
        if not PDFMINER_AVAILABLE:
            raise ImportError("pdfminer.six library not available")
        
        try:
            # Extract text with pdfminer
            return pdfminer_extract_text(str(pdf_path))
            
        except Exception as e:
            logger.error(f"PDFMiner extraction error for {pdf_path.name}: {str(e)}")
            raise
    
    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a file.
        
        This method extracts basic file metadata such as size, last modified
        time, and generates a unique file ID based on the file path and stats.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            stats = file_path.stat()
            file_hash = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()
            
            return {
                "filename": file_path.name,
                "file_path": str(file_path.absolute()),
                "file_size": stats.st_size,
                "last_modified": stats.st_mtime,
                "file_id": file_hash
            }
            
        except Exception as e:
            logger.warning(f"Error getting file metadata for {file_path}: {str(e)}")
            return {
                "filename": file_path.name,
                "file_path": str(file_path.absolute()),
                "file_id": str(uuid.uuid4())
            }


def create_pdf_processor(
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> PDFProcessor:
    """
    Create and initialize a PDF processor (convenience function).
    
    This function provides a simple interface for creating a PDFProcessor
    with default or custom settings for chunk size and overlap.
    
    Args:
        chunk_size: Maximum chunk size for text preprocessing
        chunk_overlap: Chunk overlap for text preprocessing
        
    Returns:
        Initialized PDFProcessor
    """
    # Use environment variables if not provided
    chunk_size = chunk_size or int(os.environ.get("CHUNK_SIZE", 500))
    chunk_overlap = chunk_overlap or int(os.environ.get("CHUNK_OVERLAP", 50))
    
    # Create text preprocessor
    preprocessor = create_text_preprocessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Create and return PDF processor
    return PDFProcessor(
        preprocessor=preprocessor,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    ) 
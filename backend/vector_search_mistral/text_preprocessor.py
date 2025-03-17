"""
Text Preprocessor for PDF content.
This module handles text preprocessing, chunking, and normalization for the extracted PDF content.
"""

import re
import logging
import nltk
from typing import List, Dict, Any, Optional
from nltk.tokenize import sent_tokenize

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download NLTK data for sentence tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class TextPreprocessor:
    """Preprocess text extracted from PDF documents."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):
        """
        Initialize the text preprocessor.
        
        Args:
            chunk_size: Maximum size of text chunks in characters
            chunk_overlap: Overlap between consecutive chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text by converting to lowercase, removing extra whitespace, etc.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters and numbers if needed
        # text = re.sub(r'[^a-z\s]', '', text)  # Uncomment to remove all non-alphabetic characters
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with specified size and overlap.
        
        Args:
            text: Input text to split into chunks
            
        Returns:
            List of text chunks
        """
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # Split into sentences first for more natural chunk boundaries
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, 
            # add current chunk to results and start a new chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous chunk
                if len(current_chunk) > self.chunk_overlap:
                    # Use the last part of the previous chunk as overlap
                    current_chunk = current_chunk[-self.chunk_overlap:] + " " + sentence
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def preprocess_document(self, document: Dict) -> List[Dict]:
        """
        Preprocess a document by extracting text, normalizing, and chunking.
        
        Args:
            document: Document dictionary from PDF processor
            
        Returns:
            List of dictionaries, each containing a text chunk and metadata
        """
        try:
            # Extract text from the document
            if 'content' not in document or 'content' not in document['content']:
                logger.error(f"Invalid document format: {document.get('filename', 'Unknown')}")
                return []
            
            text = document['content']['content']
            
            # Normalize text
            normalized_text = self.normalize_text(text)
            
            # Chunk the text
            chunks = self.chunk_text(normalized_text)
            
            # Create result list with chunks and metadata
            result = []
            for i, chunk in enumerate(chunks):
                result.append({
                    "chunk_id": i,
                    "text": chunk,
                    "filename": document.get("filename", "Unknown"),
                    "document_id": document.get("document_id", "Unknown"),
                    "file_path": document.get("file_path", "Unknown"),
                    "chunk_count": len(chunks)
                })
            
            logger.info(f"Created {len(chunks)} chunks for document: {document.get('filename', 'Unknown')}")
            return result
        
        except Exception as e:
            logger.error(f"Error preprocessing document: {str(e)}")
            return []
    
    def preprocess_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Preprocess multiple documents.
        
        Args:
            documents: List of document dictionaries from PDF processor
            
        Returns:
            List of dictionaries, each containing a text chunk and metadata
        """
        all_chunks = []
        for document in documents:
            document_chunks = self.preprocess_document(document)
            all_chunks.extend(document_chunks)
        
        logger.info(f"Created a total of {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks


def main():
    """Test the text preprocessor with a sample text."""
    sample_text = """
    This is a sample text for testing the text preprocessor.
    It contains multiple sentences that should be split into chunks.
    Each chunk should have a maximum size and some overlap with the next chunk.
    The preprocessor should also normalize the text by converting it to lowercase and removing extra whitespace.
    This helps improve the quality of embeddings and search results.
    Let's add more sentences to make this text longer and force it to be split into multiple chunks.
    Chunking is important for large documents as it allows us to process and search them more effectively.
    Each chunk can be independently vectorized and indexed for efficient retrieval.
    This approach is commonly used in RAG (Retrieval Augmented Generation) systems.
    """
    
    processor = TextPreprocessor(chunk_size=200, chunk_overlap=50)
    
    # Test normalization
    normalized = processor.normalize_text(sample_text)
    print(f"Normalized text (sample): {normalized[:100]}...")
    
    # Test chunking
    chunks = processor.chunk_text(normalized)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}/{len(chunks)}: {chunk[:50]}...")


if __name__ == "__main__":
    main() 
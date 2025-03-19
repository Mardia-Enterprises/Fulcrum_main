"""
Text Preprocessor for Vector Search
-------------------------------------------------------------------------------
This module handles the preprocessing of text extracted from documents before
embedding generation. It provides functionality for cleaning, splitting,
and normalizing text to optimize vector representation and search performance.

The preprocessing pipeline applies various transformations to raw text:
1. Text cleaning (removing noise, fixing encoding issues)
2. Sentence segmentation for coherent chunks
3. Chunk creation with configurable size and overlap
4. Metadata enrichment for improved search context

Key features:
- Robust text cleaning and normalization
- Intelligent text chunking with overlap control
- Sentence-aware segmentation (preserves context)
- Production-ready error handling
"""

import os
import logging
import sys
import re
from typing import List, Dict, Any, Union, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("text_preprocessor")

# Import NLTK with error handling
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    logger.warning("NLTK package not found. Install with: pip install nltk")
    NLTK_AVAILABLE = False
    nltk = None
    sent_tokenize = None

# Simple sentence splitting function for when NLTK is not available
def simple_sentence_split(text):
    """Split text into sentences using simple rules when NLTK is not available."""
    if not text:
        return []
    # Split on common sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# Default settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_MIN_CHUNK_SIZE = 50

class TextPreprocessor:
    """
    Process and prepare text for embedding generation.
    
    This class handles the cleaning, normalization, and chunking of text
    extracted from documents to prepare it for embedding generation.
    """
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        use_nltk: bool = True
    ):
        """
        Initialize the text preprocessor.
        
        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            use_nltk: Whether to use NLTK for sentence tokenization
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_nltk = use_nltk and NLTK_AVAILABLE
        
        # Ensure NLTK punkt tokenizer is available if needed
        if self.use_nltk:
            self._ensure_nltk_resources()
        
        logger.info(f"Initialized TextPreprocessor (chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, use_nltk={use_nltk})")
    
    def _ensure_nltk_resources(self):
        """
        Ensure required NLTK resources are available.
        
        This method checks if the punkt tokenizer is downloaded and
        downloads it if necessary. It handles errors gracefully.
        """
        try:
            # Check if punkt is available
            nltk.data.find('tokenizers/punkt')
            logger.info("NLTK punkt tokenizer is available")
        except LookupError:
            try:
                # Try to download punkt
                logger.info("Downloading NLTK punkt tokenizer...")
                nltk.download('punkt', quiet=True)
                logger.info("NLTK punkt tokenizer downloaded successfully")
            except Exception as e:
                logger.warning(f"Failed to download NLTK punkt tokenizer: {str(e)}")
                logger.warning("Falling back to simple sentence splitting")
                self.use_nltk = False
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process text for embedding generation.
        
        This method applies the full preprocessing pipeline to prepare text
        for embedding generation, including cleaning and chunking.
        
        Args:
            text: Raw text to process
            metadata: Additional metadata to include with the processed text
            
        Returns:
            Dictionary with processed text and metadata
        """
        if not text:
            logger.warning("Empty text provided for processing")
            return {"text": "", "chunks": [], "metadata": metadata or {}}
        
        # Clean the text
        cleaned_text = self.clean_text(text)
        
        # Split the text into chunks
        chunks = self.split_text(cleaned_text)
        
        logger.info(f"Processed text into {len(chunks)} chunks")
        
        return {
            "text": cleaned_text,
            "chunks": chunks,
            "metadata": metadata or {}
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        This method applies various text cleaning operations to improve
        the quality of text for embedding generation.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Basic text cleaning operations
        cleaned = text
        
        # Fix encoding issues
        cleaned = re.sub(r'[^\x00-\x7F]+', ' ', cleaned)  # Remove non-ASCII characters
        
        # Replace multiple spaces with a single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Fix common PDF extraction issues
        cleaned = re.sub(r'(\w)-\s+(\w)', r'\1\2', cleaned)  # Fix hyphenated words
        
        # Normalize whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.
        
        This method breaks down text into smaller chunks suitable for embedding
        generation, respecting sentence boundaries when possible.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Split text into sentences
        sentences = self._split_into_sentences(text)
        
        # Create chunks from sentences
        chunks = self._create_chunks_from_sentences(sentences)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        This method uses NLTK's sentence tokenizer if available, with a fallback
        to basic regex-based sentence splitting.
        
        Args:
            text: Text to split into sentences
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Use NLTK for sentence tokenization if available
        if self.use_nltk:
            try:
                return sent_tokenize(text)
            except Exception as e:
                logger.warning(f"Error using NLTK sentence tokenizer: {str(e)}")
                logger.warning("Falling back to simple sentence splitting")
        
        # Fallback: Use simple sentence splitting
        return simple_sentence_split(text)
    
    def _create_chunks_from_sentences(self, sentences: List[str]) -> List[str]:
        """
        Create chunks from sentences with specified size and overlap.
        
        This method combines sentences into chunks while respecting the
        configured chunk size and overlap parameters.
        
        Args:
            sentences: List of sentences to combine into chunks
            
        Returns:
            List of text chunks
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If adding this sentence would exceed the chunk size and we already have content,
            # finish the current chunk and start a new one
            if current_size + sentence_len > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # For overlap, keep some sentences from the previous chunk
                overlap_size = 0
                overlap_sentences = []
                
                # Add sentences from the end until we reach the desired overlap
                for i in range(len(current_chunk) - 1, -1, -1):
                    overlap_size += len(current_chunk[i])
                    overlap_sentences.insert(0, current_chunk[i])
                    
                    if overlap_size >= self.chunk_overlap:
                        break
                
                # Start new chunk with overlap sentences
                current_chunk = overlap_sentences
                current_size = sum(len(s) for s in current_chunk)
            
            # Add the current sentence to the chunk
            current_chunk.append(sentence)
            current_size += sentence_len
        
        # Add the last chunk if it's not empty
        if current_chunk and current_size >= DEFAULT_MIN_CHUNK_SIZE:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def is_valid_text(self, text: str) -> bool:
        """
        Check if text is valid for processing.
        
        This method performs basic validation to ensure the text is suitable
        for embedding generation.
        
        Args:
            text: Text to validate
            
        Returns:
            True if the text is valid, False otherwise
        """
        if not text or not text.strip():
            return False
        
        # Check for minimum content
        if len(text.strip()) < DEFAULT_MIN_CHUNK_SIZE:
            return False
        
        # Check for minimum word count
        word_count = len(text.split())
        if word_count < 5:
            return False
        
        # Check for sufficient alphanumeric content
        alpha_count = sum(c.isalnum() for c in text)
        if alpha_count / len(text) < 0.5:
            return False
        
        return True

    def _split_text_simple(self, text: str) -> List[str]:
        """
        Split text into sentences using simple regex rules.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        return simple_sentence_split(text)

    def _extract_person_information(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract information about a person from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with extracted person information if found
        """
        try:
            # Try to use standard punkt, not punkt_tab which is rarely available
            from nltk.tokenize import word_tokenize
            
            # Simple person name detection using heuristics
            words = word_tokenize(text.lower())
            
            # Look for person name patterns
            # This is a simplified approach
            return None  # Not implemented in this example
            
        except Exception as e:
            logger.debug(f"Error extracting person information: {str(e)}")
            return None


def create_text_preprocessor(
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    use_nltk: bool = True
) -> TextPreprocessor:
    """
    Create and initialize a text preprocessor (convenience function).
    
    This function provides a simple interface for creating a TextPreprocessor
    with default or custom settings for chunk size and overlap.
    
    Args:
        chunk_size: Maximum number of characters per chunk
        chunk_overlap: Number of characters to overlap between chunks
        use_nltk: Whether to use NLTK for sentence tokenization
        
    Returns:
        Initialized TextPreprocessor
    """
    # Use environment variables if not provided
    chunk_size = chunk_size or int(os.environ.get("CHUNK_SIZE", DEFAULT_CHUNK_SIZE))
    chunk_overlap = chunk_overlap or int(os.environ.get("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP))
    
    # Create and return the preprocessor
    return TextPreprocessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        use_nltk=use_nltk
    )

if __name__ == "__main__":
    # Example usage
    example_text = """
    This is a sample text for testing the TextPreprocessor class. 
    It contains multiple sentences. Each sentence will be processed.
    Some sentences are short. Others are much longer and contain more information that needs to be processed carefully.
    The TextPreprocessor class should handle all of these cases correctly.
    """
    
    preprocessor = TextPreprocessor(chunk_size=100, chunk_overlap=20)
    result = preprocessor.process_text(example_text)
    
    print(f"Processed text into {len(result['chunks'])} chunks:")
    for i, chunk in enumerate(result['chunks']):
        print(f"Chunk {i+1} ({len(chunk)} chars): {chunk}") 
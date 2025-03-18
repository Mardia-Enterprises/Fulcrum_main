"""
Text Preprocessor for PDF content.
This module handles text preprocessing, chunking, and normalization for the extracted PDF content.
"""

import re
import logging
import nltk
import ssl
import os
import sys
import uuid
import string
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Define a simple sentence tokenizer function
def simple_sentence_tokenizer(text):
    """Simple sentence tokenizer that splits on period, exclamation, and question marks"""
    return re.split(r'(?<=[.!?])\s+', text)

# Import NLTK
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    
    # Check if punkt tokenizer is available
    try:
        nltk.data.find('tokenizers/punkt')
        logger.info("Using NLTK punkt tokenizer")
    except LookupError:
        # Fall back to simple tokenizer
        logger.warning("NLTK punkt tokenizer not found, using simple tokenizer")
        sent_tokenize = simple_sentence_tokenizer
except ImportError:
    logger.warning("NLTK package not found, using simple sentence tokenizer")
    sent_tokenize = simple_sentence_tokenizer

class TextPreprocessor:
    """
    Preprocesses text for embedding generation.
    """
    
    def __init__(
        self, 
        chunk_size: int = 512, 
        chunk_overlap: int = 128
    ):
        """
        Initialize the text preprocessor.
        
        Args:
            chunk_size: Maximum size of text chunks in characters
            chunk_overlap: Overlap between consecutive chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Initialized TextPreprocessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def process_text(self, text: str) -> List[str]:
        """
        Process text by cleaning and splitting it into chunks.
        
        Args:
            text: Input text to process
            
        Returns:
            List of text chunks
        """
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Split text into chunks
        chunks = self._split_text(cleaned_text)
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and special characters.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?"\'-]', ' ', text)
        
        return text
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks of approximately equal size.
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        # If text is short enough, return as a single chunk
        if len(text) <= self.chunk_size:
            return [text]
            
        # Split text into sentences
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            logger.error(f"Error splitting text into sentences: {str(e)}")
            # Fall back to simple split by periods
            sentences = text.split('. ')
            sentences = [s + '.' for s in sentences[:-1]] + [sentences[-1]]
        
        # Initialize variables
        chunks = []
        current_chunk = []
        current_length = 0
        
        # Process each sentence
        for sentence in sentences:
            sentence = sentence.strip()
            sentence_length = len(sentence)
            
            # Skip empty sentences
            if sentence_length == 0:
                continue
            
            # If the sentence is longer than the chunk size, split it further
            if sentence_length > self.chunk_size:
                # If we have content in the current chunk, add it to chunks
                if current_length > 0:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split long sentence into smaller pieces
                words = sentence.split()
                current_piece = []
                current_piece_length = 0
                
                for word in words:
                    word_length = len(word) + 1  # +1 for the space
                    
                    if current_piece_length + word_length <= self.chunk_size:
                        current_piece.append(word)
                        current_piece_length += word_length
                    else:
                        chunks.append(' '.join(current_piece))
                        current_piece = [word]
                        current_piece_length = word_length
                
                # Add any remaining piece
                if current_piece:
                    chunks.append(' '.join(current_piece))
                
            # If adding the sentence to the current chunk would exceed the chunk size,
            # start a new chunk
            elif current_length + sentence_length + 1 > self.chunk_size:  # +1 for space
                # Add the current chunk to the list of chunks
                chunks.append(' '.join(current_chunk))
                
                # Start a new chunk with overlap
                overlap_size = min(self.chunk_overlap, current_length)
                if overlap_size > 0:
                    # Calculate how many sentences to keep for overlap
                    overlap_length = 0
                    overlap_sentences = []
                    
                    for i in range(len(current_chunk) - 1, -1, -1):
                        overlap_sent = current_chunk[i]
                        overlap_sent_length = len(overlap_sent) + 1  # +1 for space
                        
                        if overlap_length + overlap_sent_length <= self.chunk_overlap:
                            overlap_sentences.insert(0, overlap_sent)
                            overlap_length += overlap_sent_length
                        else:
                            break
                    
                    current_chunk = overlap_sentences
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0
                
                # Add the current sentence
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space
            
            # Otherwise, add the sentence to the current chunk
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1  # +1 for space
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # If we ended up with no chunks (unlikely), return the original text as a single chunk
        if not chunks:
            return [text]
            
        return chunks

if __name__ == "__main__":
    # Example usage
    example_text = """
    This is a sample text for testing the TextPreprocessor class. 
    It contains multiple sentences. Each sentence will be processed.
    Some sentences are short. Others are much longer and contain more information that needs to be processed carefully.
    The TextPreprocessor class should handle all of these cases correctly.
    """
    
    preprocessor = TextPreprocessor(chunk_size=100, chunk_overlap=20)
    chunks = preprocessor.process_text(example_text)
    
    print(f"Split into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} ({len(chunk)} chars): {chunk}") 
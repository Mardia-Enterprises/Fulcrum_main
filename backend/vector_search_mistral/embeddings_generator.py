"""
Embeddings Generator for Vector Search
-------------------------------------------------------------------------------
This module generates vector embeddings for text using the Mistral AI's embedding model.
It provides robust functionality for converting text chunks into vector embeddings
that can be used for semantic search and retrieval.

In production environments, this module connects to Mistral's API to generate
high-quality embeddings.

Key features:
- Production-ready embedding generation with Mistral AI
- Robust error handling and retries
- Batched processing for efficiency
"""

import os
import logging
import sys
import time
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("embeddings_generator")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not installed. Using system environment variables.")

# Import Mistral with error handling
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    logger.error("Mistral AI package not found. Install with: pip install mistralai>=1.5.0")
    MISTRAL_AVAILABLE = False
    Mistral = None

# Default settings
DEFAULT_EMBEDDING_MODEL = "mistral-embed"
DEFAULT_BATCH_SIZE = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

class EmbeddingsGenerator:
    """
    Generate vector embeddings for text chunks using Mistral AI's embedding model.
    
    This class provides an interface to Mistral's embedding API for production use.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize the embeddings generator.
        
        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model_name: Name of the embedding model to use
            batch_size: Number of texts to process in a single API call
            max_retries: Maximum number of retries for API calls
            retry_delay: Base delay between retries (in seconds)
        """
        # Get API key from environment variables if not provided
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        
        # Initialize client
        if not MISTRAL_AVAILABLE:
            logger.error("Mistral AI package not available. Cannot generate embeddings.")
            raise ImportError("Mistral AI package is required but not installed. Install with: pip install mistralai>=1.5.0")
        
        if not self.api_key:
            logger.error("Mistral API key not provided and not found in environment variables.")
            raise ValueError("Mistral API key is required. Set MISTRAL_API_KEY environment variable or provide api_key parameter.")
        
        try:
            self.client = Mistral(api_key=self.api_key)
            logger.info(f"Initialized EmbeddingsGenerator with model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing Mistral client: {str(e)}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        
        This method processes the texts in batches for efficiency and
        applies retry logic for robustness in production environments.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors, one for each input text
        """
        if not texts:
            logger.warning("Empty text list provided for embedding generation.")
            return []
        
        # Process texts in batches
        all_embeddings = []
        batch_start = 0
        
        while batch_start < len(texts):
            batch_end = min(batch_start + self.batch_size, len(texts))
            batch_texts = texts[batch_start:batch_end]
            
            # Generate embeddings for the batch with retry logic
            batch_embeddings = self._generate_batch_with_retry(batch_texts)
            all_embeddings.extend(batch_embeddings)
            
            batch_start = batch_end
            
        logger.info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def _generate_batch_with_retry(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with retry logic.
        
        Args:
            texts: Batch of text chunks to embed
            
        Returns:
            List of embedding vectors for the batch
            
        Raises:
            Exception: If embeddings cannot be generated after max retries
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Use the new embeddings.create API
                response = self.client.embeddings.create(
                    model=self.model_name,
                    inputs=texts
                )
                
                # Extract and return the embedding data
                return [item.embedding for item in response.data]
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Log the error
                logger.warning(f"Embedding API call failed (attempt {retry_count}/{self.max_retries}): {str(e)}")
                
                # Exponential backoff
                if retry_count < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
        
        # If we've exhausted retries, log and raise the error
        logger.error(f"Embedding generation failed after {self.max_retries} attempts: {str(last_error)}")
        raise last_error
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate an embedding for a single query text.
        
        This is a convenience method for generating an embedding for a search query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector for the query
        """
        if not query.strip():
            logger.warning("Empty query provided for embedding generation.")
            return [0.0] * 1024  # Return a zero vector of the expected dimension
        
        embeddings = self.generate_embeddings([query])
        return embeddings[0] if embeddings else [0.0] * 1024


def create_embeddings_generator(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> EmbeddingsGenerator:
    """
    Create and initialize an embeddings generator (convenience function).
    
    This function provides a simple interface for creating an EmbeddingsGenerator
    with default settings appropriate for production use.
    
    Args:
        api_key: Mistral API key
        model_name: Name of the embedding model to use
        
    Returns:
        Initialized EmbeddingsGenerator
    """
    # Use environment variables if not provided
    api_key = api_key or os.environ.get("MISTRAL_API_KEY")
    model_name = model_name or os.environ.get("MISTRAL_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    
    # Create and return the generator
    return EmbeddingsGenerator(
        api_key=api_key,
        model_name=model_name
    )

if __name__ == "__main__":
    # Example usage
    generator = EmbeddingsGenerator()
    document = {
        "id": "example_doc",
        "text": "This is an example document for testing embeddings generation.",
        "chunks": [
            "This is the first chunk for testing.",
            "This is the second chunk for testing.",
            "This is the third chunk for testing."
        ],
        "metadata": {
            "filename": "example.txt",
            "source": "test"
        }
    }
    
    embedded_docs = generator.generate_embeddings(document["text"])
    print(f"Generated embeddings for {len(embedded_docs)} chunks")
    
    query_embedding = generator.generate_query_embedding("What is an example?")
    print(f"Query embedding dimension: {len(query_embedding)}") 
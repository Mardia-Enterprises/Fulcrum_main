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
        
        # Check if we're passing a flag indicating we should skip retries
        # This will be set by the outer function when it detects persistent rate limiting
        skip_retries = getattr(self, '_skip_retries', False)
        
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
                error_str = str(e).lower()
                retry_count += 1
                
                # Check if this is a rate limit error
                is_rate_limit = any(marker in error_str for marker in 
                                   ["rate limit", "429", "too many requests", "quota exceeded"])
                
                # If we're in skip_retries mode and this is a rate limit error,
                # don't retry at all - immediately bubble up the error
                if skip_retries and is_rate_limit:
                    logger.warning("Rate limit detected while in skip_retries mode. Not retrying.")
                    raise e
                
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
    
    def generate_embeddings_with_partial_results(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings with support for partial results on rate limit errors.
        
        This method processes texts in smaller batches and returns both successfully
        generated embeddings and failed texts, allowing the caller to save partial
        results when rate limits are hit.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            Dictionary containing:
                - 'embeddings': List of successfully generated embeddings
                - 'failed_texts': List of texts that failed embedding generation
                - 'success_count': Number of successfully generated embeddings
                - 'failure_count': Number of failed embedding generations
                - 'completed': Boolean indicating if all texts were processed
        """
        if not texts:
            logger.warning("Empty text list provided for embedding generation.")
            return {
                "embeddings": [],
                "failed_texts": [],
                "success_count": 0,
                "failure_count": 0,
                "completed": True
            }
        
        # Use smaller batch size for better fault tolerance
        actual_batch_size = min(self.batch_size, 5)
        
        # Process texts in batches
        successful_embeddings = []
        failed_texts = []
        rate_limited = False
        
        # Keep track of rate limit errors to prevent endless loops
        rate_limit_errors = 0
        max_rate_limit_errors = 3  # Maximum number of rate limit errors before giving up
        consecutive_rate_limit_errors = 0
        max_consecutive_rate_limit_errors = 2  # Stop after 2 consecutive rate limit errors
        
        batch_start = 0
        while batch_start < len(texts) and not rate_limited:
            batch_end = min(batch_start + actual_batch_size, len(texts))
            batch_texts = texts[batch_start:batch_end]
            
            try:
                # If we're seeing too many consecutive rate limit errors,
                # set a flag to skip retries in the inner function
                self._skip_retries = (consecutive_rate_limit_errors >= max_consecutive_rate_limit_errors)
                
                # Generate embeddings for the batch with retry logic
                batch_embeddings = self._generate_batch_with_retry(batch_texts)
                successful_embeddings.extend(batch_embeddings)
                
                logger.info(f"Generated {len(batch_embeddings)} embeddings (batch {batch_start//actual_batch_size + 1})")
                
                # Successfully processed a batch, reset the consecutive error counter
                consecutive_rate_limit_errors = 0
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if this is a rate limit error
                is_rate_limit = any(marker in error_str for marker in 
                                   ["rate limit", "429", "too many requests", "quota exceeded"])
                
                if is_rate_limit:
                    rate_limit_errors += 1
                    consecutive_rate_limit_errors += 1
                    logger.warning(f"Rate limit error ({rate_limit_errors}/{max_rate_limit_errors}), consecutive: {consecutive_rate_limit_errors}")
                    
                    if rate_limit_errors >= max_rate_limit_errors or consecutive_rate_limit_errors >= max_consecutive_rate_limit_errors:
                        logger.warning("Rate limit threshold reached. Stopping embedding generation.")
                        rate_limited = True
                    else:
                        # Add exponential backoff between retries for rate limits with longer delays
                        wait_time = 10 * (2 ** (consecutive_rate_limit_errors - 1))  # 10, 20, 40 seconds
                        logger.info(f"Waiting {wait_time} seconds before continuing...")
                        time.sleep(wait_time)
                        # Don't advance the batch on first consecutive error, but do on subsequent ones
                        if consecutive_rate_limit_errors == 1:
                            continue
                
                # Add current batch to failed texts
                failed_texts.extend(batch_texts)
                
                # For rate limit errors with threshold reached, also add all remaining texts
                if is_rate_limit and rate_limited:
                    failed_texts.extend(texts[batch_end:])
                    logger.warning(f"Rate limit threshold exceeded. Stopping after processing {len(successful_embeddings)} embeddings.")
                    break
                else:
                    # For other errors, log and continue to next batch
                    logger.error(f"Error generating embeddings for batch: {str(e)}")
            
            # Advance to next batch
            batch_start = batch_end
        
        # Clean up the skip_retries flag
        if hasattr(self, '_skip_retries'):
            delattr(self, '_skip_retries')
        
        success_count = len(successful_embeddings)
        failure_count = len(failed_texts)
        completed = (success_count + failure_count) >= len(texts)
        
        logger.info(f"Embedding generation summary: {success_count} successful, {failure_count} failed")
        
        return {
            "embeddings": successful_embeddings,
            "failed_texts": failed_texts,
            "success_count": success_count,
            "failure_count": failure_count,
            "completed": completed and not rate_limited
        }


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
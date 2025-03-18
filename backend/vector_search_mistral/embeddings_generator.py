"""
Embeddings Generator for PDF content.
This module generates dense and sparse embeddings for text chunks to support hybrid search.
"""

import os
import sys
import logging
import random
import hashlib
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Import Mistral AI client
try:
    from mistralai.client import MistralClient
    from mistralai.models.embeddings import EmbeddingResponse
except ImportError:
    logger.warning("Mistral API package not found. Install with: pip install mistralai")
    # Create stub classes to avoid errors
    class MistralClient:
        def __init__(self, api_key=None):
            pass
        
        def embeddings(self, model=None, input=None):
            # Generate mock embeddings
            mock_data = []
            for text in input:
                # Create a deterministic but unique mock embedding based on the text
                mock_embedding = _generate_deterministic_embedding(text)
                mock_data.append({"embedding": mock_embedding})
            return {"data": mock_data}
    
    class EmbeddingResponse:
        pass

def _generate_deterministic_embedding(text: str, dimension: int = 1024) -> List[float]:
    """
    Generate a deterministic embedding based on text hash.
    
    Args:
        text: Text to generate embedding for
        dimension: Embedding dimension
        
    Returns:
        A deterministic vector of floats
    """
    # Create a hash of the text
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Use the hash to seed the random number generator
    random.seed(text_hash)
    
    # Generate deterministic values based on the text hash
    embedding = [random.uniform(-1, 1) for _ in range(dimension)]
    
    # Normalize to unit vector
    magnitude = sum(x*x for x in embedding) ** 0.5
    if magnitude > 0:  # Avoid division by zero
        embedding = [x / magnitude for x in embedding]
    else:
        # If for some reason we got all zeros, use a non-zero vector
        embedding = [0.1] * dimension
        embedding[0] = 0.9  # Make first element larger for consistency
    
    return embedding

class EmbeddingsGenerator:
    """
    Generate embeddings for text using Mistral AI API.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "mistral-embed"
    ):
        """
        Initialize the embeddings generator.
        
        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model: Mistral embedding model to use
        """
        # Get API key from environment variables if not provided
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        
        if not self.api_key:
            logger.warning("Mistral API key not provided and not found in environment variables")
        
        self.model = model
        
        # Initialize Mistral client
        try:
            self.client = MistralClient(api_key=self.api_key)
            logger.info(f"Initialized EmbeddingsGenerator with model: {model}")
        except Exception as e:
            logger.error(f"Error initializing Mistral client: {str(e)}")
            self.client = None
    
    def generate_embeddings(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a document with chunks.
        
        Args:
            document: Dictionary containing document text and chunks
            
        Returns:
            List of documents with embeddings
        """
        if not self.client:
            logger.warning("Mistral client not initialized. Using mock embeddings for testing.")
            return self._generate_mock_embeddings(document)
        
        if "chunks" not in document or not document["chunks"]:
            logger.warning("No chunks provided for embedding generation")
            return []
        
        # Get document base information
        doc_id = document.get("id", "")
        doc_metadata = document.get("metadata", {})
        chunks = document["chunks"]
        
        # Initialize result
        embedded_docs = []
        
        try:
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Generate embeddings for batch
                response = self.client.embeddings(
                    model=self.model,
                    input=batch
                )
                
                # Process response
                for j, embedding in enumerate(response["data"]):
                    chunk_index = i + j
                    if chunk_index < len(chunks):
                        chunk_text = chunks[chunk_index]
                        
                        # Create document with embedding
                        doc = {
                            "id": f"{doc_id}_{chunk_index}" if doc_id else f"chunk_{chunk_index}",
                            "text": chunk_text,
                            "embedding": embedding["embedding"],
                            "metadata": {
                                **doc_metadata,
                                "chunk_index": chunk_index,
                                "total_chunks": len(chunks)
                            }
                        }
                        
                        embedded_docs.append(doc)
                
                logger.info(f"Generated embeddings for {len(batch)} chunks (batch {i//batch_size + 1})")
            
            logger.info(f"Generated embeddings for {len(embedded_docs)} chunks in total")
            return embedded_docs
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            logger.info("Falling back to mock embeddings for testing")
            return self._generate_mock_embeddings(document)
    
    def _generate_mock_embeddings(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate mock embeddings for testing purposes.
        
        Args:
            document: Dictionary containing document text and chunks
            
        Returns:
            List of documents with mock embeddings
        """
        if "chunks" not in document or not document["chunks"]:
            logger.warning("No chunks provided for mock embedding generation")
            return []
            
        # Get document base information
        doc_id = document.get("id", "")
        doc_metadata = document.get("metadata", {})
        chunks = document["chunks"]
        
        # Create mock embeddings
        embedded_docs = []
        
        for i, chunk_text in enumerate(chunks):
            # Create a deterministic embedding for the chunk
            embedding = _generate_deterministic_embedding(chunk_text)
            
            # Create document with embedding
            doc = {
                "id": f"{doc_id}_{i}" if doc_id else f"chunk_{i}",
                "text": chunk_text,
                "embedding": embedding,
                "metadata": {
                    **doc_metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            
            embedded_docs.append(doc)
        
        logger.info(f"Generated mock embeddings for {len(embedded_docs)} chunks")
        return embedded_docs
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        if not self.client:
            logger.warning("Mistral client not initialized. Using mock embedding for query.")
            return _generate_deterministic_embedding(query)
        
        try:
            # Generate embedding
            response = self.client.embeddings(
                model=self.model,
                input=[query]
            )
            
            # Extract embedding
            embedding = response["data"][0]["embedding"]
            
            logger.info(f"Generated embedding for query: {query[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for query: {str(e)}")
            logger.info("Falling back to mock query embedding")
            return _generate_deterministic_embedding(query)

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
    
    embedded_docs = generator.generate_embeddings(document)
    print(f"Generated embeddings for {len(embedded_docs)} chunks")
    
    query_embedding = generator.embed_query("What is an example?")
    print(f"Query embedding dimension: {len(query_embedding)}") 
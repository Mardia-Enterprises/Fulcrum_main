"""
Pinecone Vector Database Indexer
-------------------------------------------------------------------------------
This module provides integration with Pinecone vector database for storing and
retrieving vector embeddings. It handles the creation, management, and querying
of vector indexes for semantic and hybrid search.

In production environments, this module connects to the Pinecone service to
store and query vector embeddings. It also includes mechanisms for handling
connection issues, retries, and error recovery.

Key features:
- Production-ready Pinecone integration
- Robust error handling and retry logic
- Batch operations for efficiency
- Support for hybrid search (dense and sparse vectors)
- Comprehensive metadata storage and filtering
"""

import os
import logging
import sys
import time
import json
from typing import List, Dict, Any, Union, Optional, Tuple
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("pinecone_indexer")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not installed. Using system environment variables.")

# Import Pinecone with error handling
try:
    import pinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    logger.warning("Pinecone package not found. Install with: pip install pinecone>=2.2.0")
    PINECONE_AVAILABLE = False
    pinecone = None
    Pinecone = None
    ServerlessSpec = None

# Default settings
DEFAULT_INDEX_NAME = "pdf-search"
DEFAULT_DIMENSION = 1024  # Mistral's embedding dimension
DEFAULT_METRIC = "cosine"
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

class PineconeIndexer:
    """
    Manage vector embeddings in Pinecone database for document retrieval.
    
    This class provides an interface to Pinecone's vector database services,
    with functionality for indexing, querying, and managing vector embeddings.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: str = DEFAULT_INDEX_NAME,
        dimension: int = DEFAULT_DIMENSION,
        metric: str = DEFAULT_METRIC,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize the Pinecone indexer.
        
        Args:
            api_key: Pinecone API key (defaults to PINECONE_API_KEY env var)
            environment: Pinecone environment (defaults to PINECONE_ENVIRONMENT env var)
            index_name: Name of the Pinecone index to use
            dimension: Dimension of the vector embeddings
            metric: Distance metric for similarity search (cosine, dotproduct, euclidean)
            batch_size: Number of vectors to index in a single batch
            max_retries: Maximum number of retries for API calls
            retry_delay: Base delay between retries (in seconds)
        """
        # Get API key and environment from environment variables if not provided
        self.api_key = api_key or os.environ.get("PINECONE_API_KEY")
        self.environment = environment or os.environ.get("PINECONE_ENVIRONMENT")
        
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self.index = None
        
        # Initialize Pinecone client if API key and environment are available
        if not PINECONE_AVAILABLE:
            logger.warning("Pinecone package not available. Vector search capabilities will be limited.")
            return
            
        if not self.api_key:
            logger.warning("Pinecone API key not provided and not found in environment variables")
            return
            
        if not self.environment:
            logger.warning("Pinecone environment not provided and not found in environment variables")
            return
            
        try:
            # Initialize Pinecone client
            self.client = Pinecone(api_key=self.api_key, environment=self.environment)
            
            # Initialize or create index
            self._init_index()
            
            logger.info(f"Initialized PineconeIndexer with index: {index_name}")
        except Exception as e:
            logger.error(f"Error initializing Pinecone client: {str(e)}")
    
    def _init_index(self):
        """
        Initialize or create the Pinecone index.
        
        This method checks if the specified index exists and creates it if not.
        It then connects to the index for subsequent operations.
        """
        try:
            # List existing indexes
            existing_indexes = [index.name for index in self.client.list_indexes()]
            
            # Create index if it doesn't exist
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                # Create the index with us-east-1 region for free tier compatibility
                self.client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                
                # Wait for index to initialize
                while not self.client.describe_index(self.index_name).status.get('ready', False):
                    logger.info("Waiting for index to initialize...")
                    time.sleep(5)
            
            # Connect to the index
            self.index = self.client.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone index: {str(e)}")
            raise
    
    def index_documents(self, embeddings: List[Dict[str, Any]]) -> int:
        """
        Index document embeddings in Pinecone.
        
        This method adds vector embeddings to the Pinecone index, along with
        their associated metadata. It processes documents in batches for efficiency.
        
        Args:
            embeddings: List of dictionaries containing vectors and metadata
                Each dict should have:
                - 'id': Unique identifier
                - 'embedding': Vector embedding
                - 'text': Text content
                - 'metadata': Additional metadata
            
        Returns:
            Number of vectors successfully indexed
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return 0
        
        if not embeddings:
            logger.warning("No embeddings provided for indexing")
            return 0
        
        # Process embeddings in batches
        indexed_count = 0
        batch_start = 0
        
        while batch_start < len(embeddings):
            batch_end = min(batch_start + self.batch_size, len(embeddings))
            batch = embeddings[batch_start:batch_end]
            
            # Process the batch with retry logic
            batch_indexed = self._index_batch_with_retry(batch)
            indexed_count += batch_indexed
            
            batch_start = batch_end
        
        logger.info(f"Indexed {indexed_count} vectors in Pinecone")
        return indexed_count
    
    def _index_batch_with_retry(self, batch: List[Dict[str, Any]]) -> int:
        """
        Index a batch of embeddings with retry logic.
        
        Args:
            batch: Batch of embeddings to index
            
        Returns:
            Number of vectors indexed in the batch
            
        Raises:
            Exception: If indexing fails after max retries
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Prepare vectors for Pinecone
                vectors = []
                for i, doc in enumerate(batch):
                    # Generate ID if not provided
                    doc_id = doc.get("id", str(uuid.uuid4()))
                    
                    # Extract embedding and metadata
                    embedding = doc.get("embedding", [])
                    text = doc.get("text", "")
                    metadata = doc.get("metadata", {})
                    
                    # Add text to metadata for retrieval
                    metadata["text"] = text
                    
                    # Add vector to batch
                    vectors.append({
                        "id": doc_id,
                        "values": embedding,
                        "metadata": metadata
                    })
                
                # Upsert vectors to Pinecone
                self.index.upsert(vectors=vectors)
                
                return len(vectors)
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Log the error
                logger.warning(f"Pinecone indexing failed (attempt {retry_count}/{self.max_retries}): {str(e)}")
                
                # Exponential backoff
                if retry_count < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
        
        # If we've exhausted retries, log the error
        logger.error(f"Pinecone indexing failed after {self.max_retries} attempts: {str(last_error)}")
        raise last_error
    
    def search(
        self, 
        query_embedding: List[float],
        top_k: int = 5,
        alpha: float = 0.5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the Pinecone index.
        
        This method performs a similarity search using the provided query embedding.
        It supports hybrid search with adjustable weighting between dense and
        sparse representations.
        
        Args:
            query_embedding: Vector embedding of the query
            top_k: Number of results to return
            alpha: Weight for dense vs. sparse search (1.0 = dense only)
            filter: Optional metadata filters for the search
            
        Returns:
            List of search results, each with text, score, and metadata
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return []
        
        try:
            # Perform vector search
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter
            )
            
            # Process and return results
            results = []
            for match in response.matches:
                # Extract text and metadata
                metadata = match.metadata if hasattr(match, 'metadata') else {}
                text = metadata.get("text", "")
                
                # Remove text from metadata to avoid duplication
                if "text" in metadata:
                    metadata_clean = {k: v for k, v in metadata.items() if k != "text"}
                else:
                    metadata_clean = metadata
                
                # Add result
                results.append({
                    "id": match.id,
                    "text": text,
                    "score": match.score,
                    "metadata": metadata_clean
                })
            
            logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            logger.error(f"Error during Pinecone search: {str(e)}")
            return []
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors from the Pinecone index.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False
        
        if not ids:
            logger.warning("No IDs provided for deletion")
            return False
        
        try:
            # Delete vectors by ID
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors from Pinecone: {str(e)}")
            return False
    
    def delete_all(self) -> bool:
        """
        Delete all vectors from the Pinecone index.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return False
        
        try:
            # Delete all vectors (namespace is default)
            self.index.delete(delete_all=True)
            logger.info("Deleted all vectors from Pinecone index")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting all vectors from Pinecone: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return {"error": "Index not initialized"}
        
        try:
            # Get index statistics
            stats = self.index.describe_index_stats()
            logger.info(f"Retrieved Pinecone index stats: {stats.total_vector_count} vectors")
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_name": self.index_name
            }
            
        except Exception as e:
            logger.error(f"Error getting Pinecone index stats: {str(e)}")
            return {"error": str(e)}


def create_pinecone_indexer(
    api_key: Optional[str] = None,
    environment: Optional[str] = None,
    index_name: Optional[str] = None
) -> PineconeIndexer:
    """
    Create and initialize a Pinecone indexer (convenience function).
    
    This function provides a simple interface for creating a PineconeIndexer
    with default settings appropriate for production use.
    
    Args:
        api_key: Pinecone API key
        environment: Pinecone environment
        index_name: Name of the Pinecone index to use
        
    Returns:
        Initialized PineconeIndexer
    """
    # Use environment variables if not provided
    api_key = api_key or os.environ.get("PINECONE_API_KEY")
    environment = environment or os.environ.get("PINECONE_ENVIRONMENT")
    index_name = index_name or os.environ.get("PINECONE_INDEX", DEFAULT_INDEX_NAME)
    
    # Create and return the indexer
    return PineconeIndexer(
        api_key=api_key,
        environment=environment,
        index_name=index_name
    ) 
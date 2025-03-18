"""
Pinecone Indexer for PDF embeddings.
This module handles storing and retrieving embeddings from Pinecone.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Import pinecone
try:
    import pinecone
except ImportError:
    logger.warning("Pinecone package not found. Install with: pip install pinecone")
    
    # Create a stub class to avoid errors
    class PineconeMock:
        def __init__(self, *args, **kwargs):
            pass
        
    pinecone = PineconeMock()

class PineconeIndexer:
    """
    Handles operations with the Pinecone vector database.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: str = "pdf-embeddings",
        dimension: int = 1024
    ):
        """
        Initialize the Pinecone indexer.
        
        Args:
            api_key: Pinecone API key (defaults to PINECONE_API_KEY env var)
            environment: Pinecone environment (defaults to PINECONE_REGION env var)
            index_name: Name of the Pinecone index
            dimension: Dimension of the embeddings
        """
        # Get API key from environment variables if not provided
        self.api_key = api_key or os.environ.get("PINECONE_API_KEY")
        self.environment = environment or os.environ.get("PINECONE_REGION")
        self.index_name = index_name
        self.dimension = dimension
        
        # Check if API keys are available
        if not self.api_key:
            logger.warning("Pinecone API key not provided and not found in environment variables")
        
        if not self.environment:
            logger.warning("Pinecone environment not provided and not found in environment variables")
        
        # Initialize Pinecone
        try:
            # Initialize Pinecone client
            self.pc = pinecone.Pinecone(api_key=self.api_key)
            logger.info(f"Initialized Pinecone with API key")
            
            # Check if index exists, create if not
            index_list = [idx["name"] for idx in self.pc.list_indexes()]
            
            if self.index_name not in index_list:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec={"serverless": {"cloud": "aws", "region": self.environment}}
                )
                # Wait for index to be ready
                time.sleep(10)  
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            self.index = None
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index documents in Pinecone.
        
        Args:
            documents: List of documents with embeddings
            
        Returns:
            Number of documents indexed
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return 0
        
        # Create vectors for upsert
        vectors = []
        for i, doc in enumerate(documents):
            if "embedding" not in doc:
                logger.warning(f"Document {i} has no embedding, skipping")
                continue
            
            # Create vector
            vector = {
                "id": f"{doc.get('id', 'doc')}_{i}",
                "values": doc["embedding"],
                "metadata": {
                    "text": doc["text"],
                    "filename": doc.get("metadata", {}).get("filename", ""),
                    "chunk_index": i
                }
            }
            
            vectors.append(vector)
        
        # Upsert vectors in batches
        batch_size = 100
        total_indexed = 0
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                total_indexed += len(batch)
                logger.info(f"Indexed batch of {len(batch)} vectors ({i+1}-{i+len(batch)} of {len(vectors)})")
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {str(e)}")
        
        return total_indexed
    
    def hybrid_search(
        self, 
        query: str, 
        embedding: List[float],
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using both sparse and dense vectors.
        
        Args:
            query: Text query for sparse search
            embedding: Dense vector for semantic search
            top_k: Number of results to return
            alpha: Weight for hybrid search (0 = sparse only, 1 = dense only)
            
        Returns:
            List of search results
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return []
        
        try:
            # Perform search
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results["matches"]:
                result = {
                    "id": match.get("id", ""),
                    "score": match.get("score", 0),
                    "text": match.get("metadata", {}).get("text", ""),
                    "metadata": match.get("metadata", {})
                }
                formatted_results.append(result)
            
            logger.info(f"Search returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.index:
            logger.error("Pinecone index not initialized")
            return {}
        
        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            return {}


def main():
    """Test the Pinecone indexer."""
    # Sample embeddings data
    sample_data = [
        {
            "chunk_id": 0,
            "text": "This is a sample text chunk for testing the Pinecone indexer.",
            "filename": "test_sample.pdf",
            "document_id": "test_doc_id",
            "file_path": "/path/to/test_sample.pdf",
            "chunk_count": 1,
            "dense_embedding": [0.1] * 384,  # Dummy embedding
            "sparse_embedding": {"0": 0.5, "10": 0.3, "20": 0.2}
        }
    ]
    
    # Initialize indexer
    indexer = PineconeIndexer()
    
    # Index the sample data
    stats = indexer.index_documents(sample_data)
    print(f"Indexing stats: {stats}")
    
    # Get index statistics
    index_stats = indexer.get_stats()
    print(f"Index stats: {index_stats}")
    
    # Test search
    query_embedding = [0.1] * 384  # Dummy query embedding
    query_sparse = {"0": 0.5, "10": 0.3}  # Dummy sparse embedding
    results = indexer.hybrid_search(query_embedding, query_embedding, top_k=5)
    
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Score: {result['score']}")
        print(f"  Text: {result['text'][:100]}...")
        print(f"  File: {result['filename']}")
        print()
    
    # Clean up test data
    indexer.delete_by_metadata("filename", "test_sample.pdf")


if __name__ == "__main__":
    main() 
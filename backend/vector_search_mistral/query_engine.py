"""
Query Engine for PDF search.
This module provides a high-level API for searching PDF documents.
"""

import os
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from pathlib import Path

# Add the parent directory to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Use absolute imports instead of relative imports
from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
from backend.vector_search_mistral.pinecone_indexer import PineconeIndexer

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class QueryEngine:
    """
    Search engine for querying indexed PDF documents.
    """
    
    def __init__(
        self,
        index_name: str = "pdf-embeddings",
        mistral_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_region: Optional[str] = None,
        model: str = "mistral-embed"
    ):
        """
        Initialize the query engine.
        
        Args:
            index_name: Name of the Pinecone index
            mistral_api_key: Mistral API key (defaults to env var)
            pinecone_api_key: Pinecone API key (defaults to env var)
            pinecone_region: Pinecone environment region (defaults to env var)
            model: Model to use for embeddings
        """
        # Get API keys from environment variables if not provided
        self.mistral_api_key = mistral_api_key or os.environ.get("MISTRAL_API_KEY")
        self.pinecone_api_key = pinecone_api_key or os.environ.get("PINECONE_API_KEY")
        self.pinecone_region = pinecone_region or os.environ.get("PINECONE_REGION")
        
        # Initialize embeddings generator and indexer
        try:
            self.embeddings_generator = EmbeddingsGenerator(api_key=self.mistral_api_key, model=model)
            logger.info(f"Initialized EmbeddingsGenerator with model: {model}")
        except Exception as e:
            logger.error(f"Error initializing EmbeddingsGenerator: {str(e)}")
            self.embeddings_generator = None
        
        try:
            self.indexer = PineconeIndexer(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_region,
                index_name=index_name
            )
            logger.info(f"Initialized PineconeIndexer with index: {index_name}")
        except Exception as e:
            logger.error(f"Error initializing PineconeIndexer: {str(e)}")
            self.indexer = None
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using hybrid search.
        
        Args:
            query: The search query
            top_k: Number of results to return
            alpha: Weight for hybrid search (higher values favor semantic search)
            
        Returns:
            List of search results with metadata
        """
        if not self.embeddings_generator or not self.indexer:
            error_msg = "Cannot perform search: "
            if not self.embeddings_generator:
                error_msg += "EmbeddingsGenerator not initialized. "
            if not self.indexer:
                error_msg += "PineconeIndexer not initialized."
            logger.error(error_msg)
            return []
        
        logger.info(f"Searching for: '{query}' (top_k={top_k}, alpha={alpha})")
        
        try:
            # Generate embeddings for the query
            query_embedding = self.embeddings_generator.embed_query(query)
            
            if not query_embedding:
                logger.error("Failed to generate embeddings for query")
                return []
            
            # Perform hybrid search
            results = self.indexer.hybrid_search(
                query=query,
                embedding=query_embedding,
                top_k=top_k,
                alpha=alpha
            )
            
            logger.info(f"Found {len(results)} results for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        return self.indexer.get_stats()


def main():
    """Test the query engine with a sample query."""
    # Sample search
    engine = QueryEngine()
    
    # Get index stats
    stats = engine.get_stats()
    print(f"Index stats: {stats}")
    
    # Define a test query
    test_query = "What are the key benefits of PDF search?"
    
    # Search
    results = engine.search(test_query, top_k=5)
    
    # Display results
    print(f"\nSearch results for: '{test_query}'")
    print(f"Found {len(results)} matching documents\n")
    
    for i, result in enumerate(results):
        print(f"Document {i+1}: {result['filename']}")
        print(f"Score: {result['score']}")
        print(f"Matches:")
        
        for j, match in enumerate(result['text_matches'][:2]):  # Show up to 2 matches
            print(f"  {j+1}. {match['text'][:200]}...")
        
        if len(result['text_matches']) > 2:
            print(f"  ... and {len(result['text_matches']) - 2} more matches")
        
        print()


if __name__ == "__main__":
    main() 
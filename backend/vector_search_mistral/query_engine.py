"""
Query Engine for Vector Search
-------------------------------------------------------------------------------
This module provides the core search functionality for the vector search system.
It integrates embedding generation with vector database querying to enable
semantic search over document content.

The query engine supports hybrid search, combining dense vector similarity
with optional filtering and enhancement capabilities. It orchestrates the
process of converting search queries into vector representations and retrieving
relevant results from the vector database.

Key features:
- Semantic search using vector embeddings
- Configurable search parameters (top-k, alpha)
- Robust error handling
- Support for query enhancement methods
"""

import os
import logging
import sys
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from dotenv import load_dotenv
from pathlib import Path

# Add the parent directory to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Use absolute imports instead of relative imports
from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
from backend.vector_search_mistral.pinecone_indexer import PineconeIndexer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("query_engine")

# Load environment variables
load_dotenv()

class QueryEngine:
    """
    Query engine for semantic search over vectorized documents.
    
    This class orchestrates the process of converting search queries into
    vector embeddings and retrieving relevant results from the vector database.
    """
    
    def __init__(
        self,
        embeddings_generator: Optional[EmbeddingsGenerator] = None,
        vector_db: Optional[PineconeIndexer] = None
    ):
        """
        Initialize the query engine.
        
        Args:
            embeddings_generator: Component for generating embeddings
            vector_db: Component for vector database operations
        """
        self.embeddings_generator = embeddings_generator or EmbeddingsGenerator()
        self.vector_db = vector_db or PineconeIndexer()
        
        logger.info("Initialized QueryEngine")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents semantically similar to the query.
        
        This method performs hybrid search using vector embeddings. The search
        combines dense vector similarity with optional filtering to find
        documents that best match the query semantically.
        
        Args:
            query: The search query text
            top_k: Number of results to return (default: 5)
            alpha: Weight for semantic search (1.0 = fully semantic, default: 0.5)
            filter: Optional metadata filters to apply to search
            
        Returns:
            List of search results, each containing text, score, and metadata
            
        Raises:
            ValueError: If query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings_generator.generate_query_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Perform hybrid search with the query embedding
            results = self.vector_db.search(
                query_embedding=query_embedding,
                top_k=top_k,
                alpha=alpha,
                filter=filter
            )
            
            logger.info(f"Found {len(results)} results for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def is_person_query(self, query: str) -> bool:
        """
        Determine if a query is asking about a specific person.
        
        Args:
            query: The search query
            
        Returns:
            True if the query is about a person, False otherwise
        """
        # Person-related keywords for detection
        person_keywords = [
            "who is", "worked on", "projects by", "person", "employee", 
            "staff", "personnel", "team member", "colleague", "manager",
            "engineer", "supervisor", "lead", "director", "worked with",
            "responsible for", "involvement", "contribution", "role of"
        ]
        
        # Convert to lowercase for case-insensitive matching
        lower_query = query.lower()
        return any(keyword in lower_query for keyword in person_keywords)
    
    def extract_person_name(self, query: str) -> Optional[str]:
        """
        Extract a person's name from the query using simple heuristics.
        
        Args:
            query: The search query
            
        Returns:
            The extracted person name if found, None otherwise
        """
        words = query.split()
        
        # Look for consecutive capitalized words (likely a full name)
        for i in range(len(words)-1):
            if (len(words[i]) > 0 and len(words[i+1]) > 0 and 
                words[i][0].isupper() and words[i+1][0].isupper()):
                return f"{words[i]} {words[i+1]}"
        
        # Look for single capitalized words that might be names
        for word in words:
            if (len(word) > 2 and word[0].isupper() and 
                word.lower() not in ["who", "what", "give", "list", "show", "tell", "find"]):
                return word
        
        return None


def create_query_engine(
    embeddings_api_key: Optional[str] = None,
    vector_db_api_key: Optional[str] = None,
    vector_db_environment: Optional[str] = None
) -> QueryEngine:
    """
    Create and initialize a query engine (convenience function).
    
    This function provides a simple interface for creating a QueryEngine
    with the necessary components initialized with the provided API keys.
    
    Args:
        embeddings_api_key: API key for the embeddings service
        vector_db_api_key: API key for the vector database service
        vector_db_environment: Environment for the vector database service
        
    Returns:
        Initialized QueryEngine
    """
    # Initialize embeddings generator
    embeddings_generator = EmbeddingsGenerator(api_key=embeddings_api_key)
    
    # Initialize vector database
    vector_db = PineconeIndexer(
        api_key=vector_db_api_key,
        environment=vector_db_environment
    )
    
    # Create and return the query engine
    return QueryEngine(
        embeddings_generator=embeddings_generator,
        vector_db=vector_db
    )


def main():
    """Test the query engine with a sample query."""
    # Sample search
    engine = QueryEngine()
    
    # Get index stats
    stats = engine.vector_db.get_stats()
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
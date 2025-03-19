"""
Query Engine for PDF Search
-------------------------------------------------------------------------------
This module provides a query engine that performs semantic searches over
vectorized PDF documents. It handles the process of converting user queries
into vector embeddings and retrieving relevant results from the vector database.

The query engine supports various search features:
1. Semantic search using vector embeddings
2. Person-entity detection for specialized queries
3. Hybrid search (dense and sparse retrieval)
4. Configurable search parameters
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

# Load environment variables
from dotenv import load_dotenv

# Try to import nltk for tokenization (with graceful fallback)
try:
    import nltk
    from nltk.tokenize import word_tokenize
    # Only download punkt if we're going to use it and it's not already downloaded
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except:
            pass
    NLTK_AVAILABLE = True
except ImportError:
    logging.warning("NLTK tokenize not available. Using simple tokenization instead.")
    NLTK_AVAILABLE = False
    # Simple word tokenization fallback
    word_tokenize = lambda x: x.split()

# Use absolute imports instead of relative imports
from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
from backend.vector_search_mistral.supabase_indexer import SupabaseIndexer

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
        vector_db: Optional[SupabaseIndexer] = None
    ):
        """
        Initialize the query engine.
        
        Args:
            embeddings_generator: Component for generating embeddings
            vector_db: Component for vector database operations
        """
        self.embeddings_generator = embeddings_generator or EmbeddingsGenerator()
        self.vector_db = vector_db or SupabaseIndexer()
        
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
        Detect if a query is asking about a specific person.
        
        Args:
            query: Query string to check
            
        Returns:
            True if this appears to be a person query, False otherwise
        """
        # Use a simpler approach with regular expressions instead of NLTK
        query = query.lower()
        
        # Common patterns for person queries
        person_patterns = [
            r"who is",
            r"about .+",
            r"what .+ (do|did|does)",
            r"where .+ work",
            r"when did .+ (join|start)",
            r"experience of",
            r"projects (by|of|from)",
            r"resume of",
            r"background of",
            r"qualification[s]? of",
        ]
        
        # Check if any pattern matches
        for pattern in person_patterns:
            if re.search(pattern, query):
                return True
        
        # Check for common keywords
        person_keywords = [
            "person", "employee", "staff", "personnel", "team member", 
            "colleague", "manager", "engineer", "supervisor", "lead", 
            "director", "worked with", "experience", "skills"
        ]
        
        return any(keyword in query for keyword in person_keywords)
    
    def extract_person_name(self, query: str) -> Optional[str]:
        """
        Extract a person's name from a query.
        
        Args:
            query: Query string that may contain a person name
            
        Returns:
            Extracted name or None if no name found
        """
        # Use regex patterns to find potential names
        import re
        
        # Common patterns for person name queries
        name_patterns = [
            r"(?:about|who is) ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"([A-Z][a-z]+ [A-Z][a-z]+)'s experience",
            r"([A-Z][a-z]+ [A-Z][a-z]+)'s qualifications",
            r"([A-Z][a-z]+ [A-Z][a-z]+)'s projects",
            r"([A-Z][a-z]+ [A-Z][a-z]+)'s resume",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Fallback: look for capitalized word pairs (potential names)
        matches = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', query)
        if matches:
            return matches[0]
        
        return None

def create_query_engine(
    embeddings_api_key: Optional[str] = None,
    vector_db_url: Optional[str] = None,
    vector_db_api_key: Optional[str] = None
) -> QueryEngine:
    """
    Create and configure a query engine with the specified parameters.
    
    Args:
        embeddings_api_key: API key for the embeddings model
        vector_db_url: URL for the vector database
        vector_db_api_key: API key for the vector database
        
    Returns:
        Configured QueryEngine instance
    """
    # Create embeddings generator with specified API key
    embeddings_generator = EmbeddingsGenerator(api_key=embeddings_api_key)
    
    # Create Supabase indexer with specified parameters
    vector_db = SupabaseIndexer(
        url=vector_db_url,
        api_key=vector_db_api_key
    )
    
    # Create query engine with configured components
    return QueryEngine(
        embeddings_generator=embeddings_generator,
        vector_db=vector_db
    )

def main():
    """
    Run a simple test query if this module is executed directly.
    """
    # Load environment variables
    load_dotenv()
    
    # Set up query engine
    query_engine = create_query_engine()
    
    # Test query
    test_query = "What are the main components of a hydraulic system?"
    print(f"Running test query: '{test_query}'")
    
    # Search with the test query
    results = query_engine.search(test_query, top_k=3)
    
    # Print results
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (score: {result['score']:.4f}):")
        print(f"Text: {result['text'][:200]}...")
        print(f"Metadata: {result['metadata']}")

if __name__ == "__main__":
    main() 
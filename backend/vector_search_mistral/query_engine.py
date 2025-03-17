"""
Query Engine for PDF search.
This module provides a high-level API for searching PDF documents.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

from .embeddings_generator import EmbeddingsGenerator
from .pinecone_indexer import PineconeIndexer

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class QueryEngine:
    """Query engine for searching PDF documents."""
    
    def __init__(self, index_name: str = "pdf-data-vector"):
        """
        Initialize the query engine.
        
        Args:
            index_name: Name of the Pinecone index to use
        """
        logger.info("Initializing query engine")
        self.embedding_generator = EmbeddingsGenerator()
        self.pinecone_indexer = PineconeIndexer(index_name=index_name)
    
    def search(self, 
               query: str, 
               top_k: int = 5, 
               alpha: float = 0.5) -> List[Dict]:
        """
        Search for documents matching the query.
        
        Args:
            query: User query
            top_k: Number of results to return
            alpha: Weight for hybrid search (0 = sparse only, 1 = dense only)
            
        Returns:
            List of search results with text matches and document info
        """
        logger.info(f"Processing query: '{query}'")
        
        try:
            # Generate query embeddings
            query_chunks = [{"text": query, "chunk_id": 0, "filename": "query", "document_id": "query", "file_path": "", "chunk_count": 1}]
            query_embeddings = self.embedding_generator.generate_hybrid_embeddings(query_chunks)[0]
            
            # Search Pinecone
            results = self.pinecone_indexer.search(
                query_text=query,
                query_embedding=query_embeddings["dense_embedding"],
                query_sparse_embedding=query_embeddings["sparse_embedding"],
                top_k=top_k,
                alpha=alpha
            )
            
            # Group results by filename
            grouped_results = self._group_results_by_file(results)
            
            # Format for display
            formatted_results = self._format_results(grouped_results)
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def _group_results_by_file(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group search results by filename.
        
        Args:
            results: List of search results
            
        Returns:
            Dictionary mapping filenames to lists of results
        """
        grouped = {}
        for result in results:
            filename = result["filename"]
            if filename not in grouped:
                grouped[filename] = []
            grouped[filename].append(result)
        
        # Sort each group by score
        for filename in grouped:
            grouped[filename].sort(key=lambda x: x["score"], reverse=True)
        
        return grouped
    
    def _format_results(self, grouped_results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Format grouped results for display.
        
        Args:
            grouped_results: Dictionary mapping filenames to lists of results
            
        Returns:
            List of formatted results
        """
        formatted = []
        
        # Sort files by highest score in each group
        sorted_files = sorted(
            grouped_results.keys(),
            key=lambda x: max([r["score"] for r in grouped_results[x]]),
            reverse=True
        )
        
        for filename in sorted_files:
            file_results = grouped_results[filename]
            top_result = file_results[0]  # Highest scoring result for this file
            
            # Collect all matching text snippets
            text_matches = []
            for result in file_results:
                text_matches.append({
                    "text": result["text"],
                    "score": result["score"],
                    "chunk_id": result["chunk_id"]
                })
            
            # Format the result
            formatted_result = {
                "filename": filename,
                "file_path": top_result["file_path"],
                "document_id": top_result["document_id"],
                "score": top_result["score"],  # Use highest score
                "text_matches": text_matches
            }
            
            formatted.append(formatted_result)
        
        return formatted
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        return self.pinecone_indexer.get_stats()


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
        print(f"Path: {result['file_path']}")
        print(f"Matches:")
        
        for j, match in enumerate(result['text_matches'][:2]):  # Show up to 2 matches
            print(f"  {j+1}. {match['text'][:200]}...")
        
        if len(result['text_matches']) > 2:
            print(f"  ... and {len(result['text_matches']) - 2} more matches")
        
        print()


if __name__ == "__main__":
    main() 
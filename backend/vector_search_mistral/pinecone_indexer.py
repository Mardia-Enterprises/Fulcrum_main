"""
Pinecone Indexer for PDF embeddings.
This module handles storing and retrieving embeddings from Pinecone.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PineconeIndexer:
    """Store and retrieve embeddings from Pinecone."""
    
    def __init__(self, index_name: str = "pdf-data-vector"):
        """
        Initialize the Pinecone indexer.
        
        Args:
            index_name: Name of the Pinecone index to use
        """
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.region = os.getenv("PINECONE_REGION")
        
        if not self.api_key or not self.region:
            raise ValueError("PINECONE_API_KEY or PINECONE_REGION not found in environment variables.")
        
        self.index_name = index_name
        
        # Initialize Pinecone
        logger.info(f"Initializing Pinecone with index: {index_name}")
        self.pc = Pinecone(api_key=self.api_key)
        
        # Check if index exists, create if not
        self._initialize_index()
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
        
    def _initialize_index(self, dimension: int = 384):
        """
        Check if index exists, create if not.
        
        Args:
            dimension: Dimension of the embeddings
        """
        # List all indexes
        indexes = self.pc.list_indexes()
        
        # Check if our index exists
        if self.index_name not in [idx.name for idx in indexes.indexes]:
            logger.info(f"Creating new Pinecone index: {self.index_name}")
            
            # Create the index
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.region
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to initialize...")
            time.sleep(10)  # Give time for index to initialize
            
            logger.info(f"Index {self.index_name} created successfully")
        else:
            logger.info(f"Using existing index: {self.index_name}")
    
    def index_embeddings(self, embeddings_data: List[Dict]) -> Dict[str, int]:
        """
        Index embeddings in batches.
        
        Args:
            embeddings_data: List of dictionaries with chunks and their embeddings
            
        Returns:
            Dictionary with counts of vectors processed, indexed, and errors
        """
        batch_size = 100  # Pinecone batch size limit
        stats = {"processed": 0, "indexed": 0, "errors": 0}
        
        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i:i+batch_size]
            vectors = []
            
            for item in batch:
                # Create a unique ID for each chunk
                vector_id = f"{item['filename']}_chunk_{item['chunk_id']}"
                
                # Prepare the metadata (everything except the embeddings)
                metadata = {
                    "chunk_id": item["chunk_id"],
                    "text": item["text"],
                    "filename": item["filename"],
                    "document_id": item["document_id"],
                    "file_path": item["file_path"],
                    "chunk_count": item["chunk_count"]
                }
                
                # Create the vector
                vector = {
                    "id": vector_id,
                    "values": item["dense_embedding"],
                    "metadata": metadata,
                    "sparse_values": {
                        "indices": list(map(int, item["sparse_embedding"].keys())),
                        "values": list(item["sparse_embedding"].values())
                    }
                }
                
                vectors.append(vector)
                stats["processed"] += 1
            
            try:
                # Upsert the batch
                self.index.upsert(vectors=vectors)
                stats["indexed"] += len(vectors)
                logger.info(f"Indexed batch of {len(vectors)} vectors")
            except Exception as e:
                logger.error(f"Error indexing batch: {str(e)}")
                stats["errors"] += len(vectors)
        
        logger.info(f"Indexing complete: processed={stats['processed']}, indexed={stats['indexed']}, errors={stats['errors']}")
        return stats
    
    def search(self, 
               query_text: str, 
               query_embedding: List[float],
               query_sparse_embedding: Dict[str, float],
               top_k: int = 5, 
               include_metadata: bool = True,
               alpha: float = 0.5) -> List[Dict]:
        """
        Search for similar documents using hybrid search.
        
        Args:
            query_text: Original query text
            query_embedding: Dense embedding of the query
            query_sparse_embedding: Sparse embedding of the query
            top_k: Number of results to return
            include_metadata: Whether to include metadata in the results
            alpha: Weight for hybrid search (0 = sparse only, 1 = dense only)
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: '{query_text}' with top_k={top_k}, alpha={alpha}")
        
        # Convert sparse embedding to the format Pinecone expects
        sparse_vector = {
            "indices": list(map(int, query_sparse_embedding.keys())),
            "values": list(query_sparse_embedding.values())
        }
        
        try:
            # Perform hybrid search
            results = self.index.query(
                vector=query_embedding,
                sparse_vector=sparse_vector,
                top_k=top_k,
                include_metadata=include_metadata,
                alpha=alpha
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                result = {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "filename": match.metadata.get("filename", ""),
                    "document_id": match.metadata.get("document_id", ""),
                    "file_path": match.metadata.get("file_path", ""),
                    "chunk_id": match.metadata.get("chunk_id", 0)
                }
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def delete_by_filename(self, filename: str) -> int:
        """
        Delete all vectors for a specific file.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            Number of vectors deleted
        """
        try:
            # List all IDs that match the filename
            response = self.index.query(
                top_k=10000,  # Large number to get all matches
                include_metadata=True,
                filter={"filename": {"$eq": filename}}
            )
            
            # Extract the IDs
            ids = [match.id for match in response.matches]
            
            if ids:
                # Delete the vectors
                self.index.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} vectors for file: {filename}")
                return len(ids)
            else:
                logger.info(f"No vectors found for file: {filename}")
                return 0
        
        except Exception as e:
            logger.error(f"Error deleting vectors for file {filename}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            return self.index.describe_index_stats()
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
    stats = indexer.index_embeddings(sample_data)
    print(f"Indexing stats: {stats}")
    
    # Get index statistics
    index_stats = indexer.get_stats()
    print(f"Index stats: {index_stats}")
    
    # Test search
    query_embedding = [0.1] * 384  # Dummy query embedding
    query_sparse = {"0": 0.5, "10": 0.3}  # Dummy sparse embedding
    results = indexer.search("test query", query_embedding, query_sparse, top_k=5)
    
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Score: {result['score']}")
        print(f"  Text: {result['text'][:100]}...")
        print(f"  File: {result['filename']}")
        print()
    
    # Clean up test data
    indexer.delete_by_filename("test_sample.pdf")


if __name__ == "__main__":
    main() 
"""
Supabase Vector Database Indexer
-------------------------------------------------------------------------------
This module provides integration with Supabase's vector database capabilities for 
storing and retrieving vector embeddings. It handles the creation, management, 
and querying of vector tables for semantic and hybrid search.

In production environments, this module connects to the Supabase service to
store and query vector embeddings. It also includes mechanisms for handling
connection issues, retries, and error recovery.

Key features:
- Production-ready Supabase integration
- Robust error handling and retry logic
- Batch operations for efficiency
- Support for hybrid search (dense vectors)
- Comprehensive metadata storage and filtering
"""

import os
import logging
import sys
import time
import json
import uuid
from typing import List, Dict, Any, Union, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("supabase_indexer")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not installed. Using system environment variables.")

# Import Supabase with error handling
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.warning("Supabase package not found. Install with: pip install supabase>=1.0.0")
    SUPABASE_AVAILABLE = False
    create_client = None

# Default settings
DEFAULT_TABLE_NAME = "pdf_documents"
DEFAULT_DIMENSION = 1024  # Mistral's embedding dimension
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

class SupabaseIndexer:
    """
    Manage vector embeddings in Supabase database for document retrieval.
    
    This class provides an interface to Supabase's vector database services,
    with functionality for indexing, querying, and managing vector embeddings.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        table_name: str = DEFAULT_TABLE_NAME,
        dimension: int = DEFAULT_DIMENSION,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        Initialize the Supabase indexer.
        
        Args:
            url: Supabase project URL (defaults to SUPABASE_PROJECT_URL env var)
            api_key: Supabase API key (defaults to SUPABASE_PRIVATE_API_KEY env var)
            table_name: Name of the Supabase table to use
            dimension: Dimension of the vector embeddings
            batch_size: Number of vectors to index in a single batch
            max_retries: Maximum number of retries for API calls
            retry_delay: Base delay between retries (in seconds)
        """
        # Get API key and URL from environment variables if not provided
        self.url = url or os.environ.get("SUPABASE_PROJECT_URL")
        self.api_key = api_key or os.environ.get("SUPABASE_PRIVATE_API_KEY")
        
        self.table_name = table_name
        self.dimension = dimension
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        
        # Check if Supabase package is available
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase package not available. Vector search capabilities will be limited.")
            return
        
        # Check if Supabase credentials are provided
        if not self.url or not self.api_key:
            logger.error("Supabase URL or API key not provided and not found in environment variables.")
            logger.error("Ensure SUPABASE_PROJECT_URL and SUPABASE_PRIVATE_API_KEY are set in the environment.")
            return
            
        # Initialize Supabase client with retry logic
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.client = create_client(self.url, self.api_key)
                logger.info(f"Initialized SupabaseIndexer with table: {table_name}")
                
                # Check if the table exists and validate it
                self._validate_table()
                
                # Successfully connected, break the retry loop
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error initializing Supabase client (attempt {retry_count}/{self.max_retries}): {str(e)}")
                
                if retry_count < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying Supabase connection in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Failed to initialize Supabase client after multiple attempts.")
                    self.client = None
    
    def _validate_table(self):
        """
        Validate that the vector table exists with the correct schema.
        If the table doesn't exist, create it.
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return
            
        try:
            # Check if the table exists
            response = self.client.table(self.table_name).select("id").limit(1).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.warning(f"Error checking table: {response.error}")
                # Table might not exist, try to create it
                self._create_table()
            else:
                logger.info(f"Successfully connected to table: {self.table_name}")
        except Exception as e:
            logger.warning(f"Error validating table: {str(e)}")
            # Try to create the table
            self._create_table()
    
    def _create_table(self):
        """
        Create the vector table with the correct schema.
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return
            
        try:
            # SQL to create the table and extension
            sql = f"""
            -- Enable the vector extension if not already enabled
            CREATE EXTENSION IF NOT EXISTS vector;
            
            -- Create the table if it doesn't exist
            CREATE TABLE IF NOT EXISTS {self.table_name} (
              id TEXT PRIMARY KEY,
              content TEXT,
              embedding VECTOR({self.dimension}),
              metadata JSONB,
              file_path TEXT,
              chunk_id TEXT,
              file_type TEXT
            );
            
            -- Create an index for efficient vector search
            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
            ON {self.table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            
            -- Create a function for similarity search
            CREATE OR REPLACE FUNCTION match_documents(
              query_embedding VECTOR({self.dimension}),
              match_threshold FLOAT,
              match_count INT
            )
            RETURNS TABLE (
              id TEXT,
              content TEXT,
              metadata JSONB,
              file_path TEXT,
              chunk_id TEXT,
              file_type TEXT,
              similarity FLOAT
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
              RETURN QUERY
              SELECT
                {self.table_name}.id,
                {self.table_name}.content,
                {self.table_name}.metadata,
                {self.table_name}.file_path,
                {self.table_name}.chunk_id,
                {self.table_name}.file_type,
                1 - ({self.table_name}.embedding <=> query_embedding) AS similarity
              FROM 
                {self.table_name}
              WHERE 
                1 - ({self.table_name}.embedding <=> query_embedding) > match_threshold
              ORDER BY
                {self.table_name}.embedding <=> query_embedding
              LIMIT match_count;
            END;
            $$;
            """
            
            # First attempt: Try to execute the SQL directly
            try:
                logger.info(f"Creating or validating table: {self.table_name}")
                response = self.client.query(sql).execute()
                if hasattr(response, 'error') and response.error:
                    raise Exception(f"Error in direct SQL execution: {response.error}")
                
                logger.info(f"Successfully created or validated table: {self.table_name}")
                return
                
            except Exception as direct_error:
                logger.warning(f"Direct SQL execution failed: {str(direct_error)}")
                logger.info("Trying alternative method for table creation...")
                
                # Second attempt: Try using Database RPC methods
                try:
                    logger.info("Trying exec_sql RPC method...")
                    response = self.client.rpc('exec_sql', {'query': sql}).execute()
                    
                    if hasattr(response, 'error') and response.error:
                        logger.warning(f"exec_sql RPC failed: {response.error}")
                        raise Exception("RPC method failed")
                    
                    logger.info(f"Successfully created table {self.table_name} via RPC")
                    return
                    
                except Exception as rpc_error:
                    logger.warning(f"exec_sql RPC method failed: {str(rpc_error)}")
                    
                    # Third attempt: Try executing statements one by one
                    try:
                        logger.info("Trying pg_execute RPC method...")
                        
                        # Split the SQL into individual statements
                        statements = sql.split(';')
                        for i, stmt in enumerate(statements):
                            if stmt.strip():
                                rpc_response = self.client.rpc(
                                    'pg_execute', 
                                    {'query': stmt + ';'}
                                ).execute()
                                
                                if hasattr(rpc_response, 'error') and rpc_response.error:
                                    logger.warning(f"Statement {i+1} failed: {rpc_response.error}")
                                    # Continue with next statement
                        
                        logger.info(f"Finished executing statements via pg_execute RPC")
                        return
                        
                    except Exception as pg_error:
                        # Final fallback - try running just the CREATE TABLE statements
                        logger.warning(f"Could not run postgres RPC: {str(pg_error)}")
                        logger.warning("Trying basic table creation without extensions or functions...")
                        
                        # Create a simple table without indexes for now
                        try:
                            basic_sql = f"""
                            CREATE TABLE IF NOT EXISTS {self.table_name} (
                              id TEXT PRIMARY KEY,
                              content TEXT,
                              embedding VECTOR({self.dimension}),
                              metadata JSONB,
                              file_path TEXT,
                              chunk_id TEXT,
                              file_type TEXT
                            );
                            """
                            self.client.query(basic_sql).execute()
                            logger.info(f"Created basic table {self.table_name} without indexes")
                            return
                        except Exception as basic_error:
                            logger.error(f"Even basic table creation failed: {str(basic_error)}")
                            logger.error("Your Supabase instance might not support vector operations")
                            logger.error("Please ensure the pgvector extension is enabled in your Supabase project")
            
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            logger.error(f"You may need to create the table manually. See the documentation.")
    
    def index_documents(self, embeddings: List[Dict[str, Any]]) -> int:
        """
        Index a batch of document embeddings into Supabase.
        
        Args:
            embeddings: List of embedding objects, each containing:
                - id: Unique identifier for the document
                - values: Vector embedding values
                - metadata: Document metadata
                
        Returns:
            Number of documents successfully indexed
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return 0
            
        if not embeddings:
            logger.warning("No embeddings provided to index")
            return 0
            
        # Track successful inserts
        successful_inserts = 0
        
        # Process embeddings in batches
        for i in range(0, len(embeddings), self.batch_size):
            batch = embeddings[i:i + self.batch_size]
            batch_size = len(batch)
            
            logger.info(f"Indexing batch of {batch_size} documents")
            
            # Index batch with retry logic
            successful = self._index_batch_with_retry(batch)
            successful_inserts += successful
            
            logger.info(f"Indexed {successful}/{batch_size} documents in batch")
            
        return successful_inserts
    
    def _index_batch_with_retry(self, batch: List[Dict[str, Any]]) -> int:
        """
        Index a batch of embeddings with retry logic.
        
        Args:
            batch: List of embedding objects to index
            
        Returns:
            Number of successfully indexed documents
        """
        # Format the data for Supabase
        formatted_data = []
        for item in batch:
            doc_id = item.get("id", str(uuid.uuid4()))
            embedding = item.get("embedding", [])
            text = item.get("text", "")
            metadata = item.get("metadata", {})
            
            # Validate the embedding vector to prevent Supabase errors
            if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                logger.warning(f"Skipping document '{doc_id}' due to invalid embedding (empty or null)")
                continue
                
            # Check vector dimensions - Supabase requires non-empty vectors
            if len(embedding) != self.dimension:
                logger.warning(f"Embedding dimension mismatch for '{doc_id}': got {len(embedding)}, expected {self.dimension}")
                # If length is wrong but not zero, try to pad or truncate
                if len(embedding) > 0:
                    if len(embedding) < self.dimension:
                        # Pad with zeros if too short
                        embedding = embedding + [0.0] * (self.dimension - len(embedding))
                        logger.warning(f"Padded embedding to {self.dimension} dimensions")
                    else:
                        # Truncate if too long
                        embedding = embedding[:self.dimension]
                        logger.warning(f"Truncated embedding to {self.dimension} dimensions")
                else:
                    # Skip if empty after all checks
                    continue
            
            # Prepare data for Supabase
            formatted_item = {
                "id": doc_id,
                "embedding": embedding,
                "content": text,
                "metadata": metadata,
                "file_path": metadata.get("file_path", ""),
                "chunk_id": metadata.get("chunk_id", ""),
                "file_type": metadata.get("file_type", "")
            }
            formatted_data.append(formatted_item)
        
        # Skip if no valid documents after filtering
        if not formatted_data:
            logger.warning("No valid documents to index after filtering")
            return 0
            
        # Retry logic
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                # Index the documents in Supabase
                response = self.client.table(self.table_name).insert(formatted_data).execute()
                
                # Check for errors in response
                if hasattr(response, 'error') and response.error:
                    raise Exception(f"Supabase error: {response.error}")
                
                logger.info(f"Indexed {len(formatted_data)}/{len(batch)} documents in batch")
                return len(formatted_data)
                
            except Exception as e:
                last_error = e
                retries += 1
                
                # Log the error
                logger.error(f"Exception during batch indexing: {str(e)}")
                
                # Exponential backoff
                if retries < self.max_retries:
                    sleep_time = self.retry_delay * (2 ** (retries - 1))
                    logger.info(f"Retrying in {sleep_time:.2f} seconds (attempt {retries}/{self.max_retries})")
                    time.sleep(sleep_time)
        
        # If we've exhausted retries, log the error
        logger.error(f"Failed to index batch after {self.max_retries} retries")
        
        # Return the number of documents indexed (0 in this case)
        return 0
    
    def search(
        self, 
        query_embedding: List[float],
        top_k: int = 5,
        alpha: float = 0.5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the Supabase database.
        
        Args:
            query_embedding: Vector embedding of the query
            top_k: Number of results to return
            alpha: Search weight factor (ignored in Supabase implementation)
            filter: Optional metadata filters to apply
            
        Returns:
            List of search results, each containing text and metadata
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
            
        if not query_embedding:
            logger.error("Query embedding cannot be empty")
            return []
            
        try:
            # Prepare filters if provided
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,  # Minimum similarity threshold
                "match_count": top_k
            }
            
            # Use different function based on whether filter is provided
            if filter:
                filter_conditions = []
                for key, value in filter.items():
                    if key == "file_path" and value:
                        filter_conditions.append(f"file_path = '{value}'")
                    elif key == "file_type" and value:
                        filter_conditions.append(f"file_type = '{value}'")
                    # Add more filter conditions as needed
                
                if filter_conditions:
                    filter_string = " AND ".join(filter_conditions)
                    rpc_params["filter_string"] = filter_string
                    
                    # Use the filtered version of the function
                    response = self.client.rpc(
                        "match_documents_filtered", 
                        rpc_params
                    ).execute()
                else:
                    # No filter conditions, use standard function
                    response = self.client.rpc(
                        "match_documents", 
                        rpc_params
                    ).execute()
            else:
                # No filter provided, use standard function
                response = self.client.rpc(
                    "match_documents", 
                    rpc_params
                ).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error during search: {response.error}")
                return []
            
            # Format the results
            results = []
            for item in response.data:
                result = {
                    "id": item.get("id"),
                    "score": item.get("similarity", 0),
                    "text": item.get("content", ""),
                    "metadata": item.get("metadata", {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by their IDs.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return False
            
        if not ids:
            logger.warning("No IDs provided for deletion")
            return False
            
        try:
            # Delete vectors in batches
            for i in range(0, len(ids), self.batch_size):
                batch_ids = ids[i:i + self.batch_size]
                
                # Delete the batch
                response = self.client.table(self.table_name).delete().in_("id", batch_ids).execute()
                
                if hasattr(response, 'error') and response.error:
                    logger.error(f"Error deleting vectors: {response.error}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error during vector deletion: {str(e)}")
            return False
    
    def delete_all(self) -> bool:
        """
        Delete all vectors from the table.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return False
            
        try:
            # This is a dangerous operation, so we log a warning
            logger.warning(f"Deleting ALL vectors from table: {self.table_name}")
            
            # Delete all records
            response = self.client.table(self.table_name).delete().neq("id", "no-match-placeholder").execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error deleting all vectors: {response.error}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error during complete deletion: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vectors in the table.
        
        Returns:
            Dictionary with statistics
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return {"status": "error", "message": "Supabase client not initialized"}
            
        try:
            # Count total vectors
            response = self.client.table(self.table_name).select("id", count="exact").execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error getting stats: {response.error}")
                return {"status": "error", "message": str(response.error)}
            
            # Extract count from response
            count = len(response.data)
            
            # Get file types
            file_types_response = self.client.table(self.table_name).select("file_type").execute()
            file_types = set()
            if not (hasattr(file_types_response, 'error') and file_types_response.error):
                for item in file_types_response.data:
                    if "file_type" in item and item["file_type"]:
                        file_types.add(item["file_type"])
            
            return {
                "status": "success",
                "vectors_count": count,
                "dimension": self.dimension,
                "file_types": list(file_types)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"status": "error", "message": str(e)}

def create_supabase_indexer(
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    table_name: Optional[str] = None
) -> SupabaseIndexer:
    """
    Create and configure a Supabase indexer instance.
    
    Args:
        url: Supabase project URL
        api_key: Supabase API key
        table_name: Name of the table to use
        
    Returns:
        Configured SupabaseIndexer instance
    """
    # Get API key and environment from environment variables if not provided
    url = url or os.environ.get("SUPABASE_PROJECT_URL")
    api_key = api_key or os.environ.get("SUPABASE_PRIVATE_API_KEY")
    table_name = table_name or os.environ.get("SUPABASE_TABLE_NAME", DEFAULT_TABLE_NAME)
    
    # Create the indexer
    return SupabaseIndexer(url=url, api_key=api_key, table_name=table_name) 
"""
PDF Vector Search Engine - Main Module
-------------------------------------------------------------------------------
This is the main module for the PDF Vector Search Engine, providing a unified 
interface to the system's functionality. It orchestrates the various components
for PDF processing, text extraction, embedding generation, vector storage, and 
semantic search.

The module is designed for production use, with robust error handling, logging,
and configuration options. It can be used as a standalone application or
integrated into larger systems.

Usage Examples:
    # Process PDFs
    python -m vector_search_mistral process --pdf-dir /path/to/pdfs
    
    # Search for content
    python -m vector_search_mistral search "your search query"
    
    # Advanced search with RAG
    python -m vector_search_mistral search "your query" --rag --rag-mode detail
"""

import os
import sys
import logging
import argparse
import json
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import time
import datetime

# Add the parent directory to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("vector_search")

# Try to load environment variables from root .env file
try:
    from dotenv import load_dotenv
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")
except ImportError:
    logger.info("python-dotenv not installed. Using system environment variables.")

# Import local modules using absolute imports
from backend.vector_search_mistral.pdf_processor import PDFProcessor, create_pdf_processor
from backend.vector_search_mistral.text_preprocessor import TextPreprocessor, create_text_preprocessor
from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
from backend.vector_search_mistral.supabase_indexer import SupabaseIndexer, create_supabase_indexer
from backend.vector_search_mistral.query_engine import QueryEngine
from backend.vector_search_mistral.openai_processor import OpenAIProcessor
from backend.vector_search_mistral.check_env import check_required_variables

# Check environment variables
def check_env_vars() -> bool:
    """
    Check if required environment variables are set.
    
    Returns:
        True if all required variables are set, False otherwise
    """
    success, missing_vars = check_required_variables()
    
    if not success:
        # Log missing variables
        logger.error(f"Missing required environment variables: {', '.join([var for var, _ in missing_vars])}")
        logger.error("Please set these variables in the root .env file")
        return False
    
    return True

def init_components() -> Tuple[PDFProcessor, EmbeddingsGenerator, SupabaseIndexer, QueryEngine]:
    """
    Initialize the main components of the system.
    
    Returns:
        Tuple of (PDFProcessor, EmbeddingsGenerator, SupabaseIndexer, QueryEngine)
    """
    # Create components
    pdf_processor = create_pdf_processor()
    embeddings_generator = EmbeddingsGenerator()
    vector_db = create_supabase_indexer()
    query_engine = QueryEngine(embeddings_generator, vector_db)
    
    return pdf_processor, embeddings_generator, vector_db, query_engine

def process_pdfs(
    pdf_dir: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    force: bool = False
) -> Dict[str, Any]:
    """
    Process PDF files in a directory for vector search.
    
    This function extracts text from PDF files, processes it into chunks,
    generates embeddings, and stores the vectors in the database.
    
    Args:
        pdf_dir: Directory containing PDF files
        chunk_size: Maximum chunk size for text preprocessing
        chunk_overlap: Chunk overlap for text preprocessing
        force: Whether to force reprocessing of existing files
        
    Returns:
        Dictionary with processing statistics
    """
    # Check if pdf_dir exists, create it if it doesn't
    if not os.path.exists(pdf_dir):
        logger.info(f"PDF directory not found: {pdf_dir}. Creating it...")
        try:
            os.makedirs(pdf_dir, exist_ok=True)
            logger.info(f"Created PDF directory: {pdf_dir}")
            logger.info(f"Please place PDF files in this directory and run the command again.")
            return {
                "status": "directory_created",
                "message": f"Created directory {pdf_dir}. Please add PDF files and run again.",
                "total_pdfs": 0,
                "total_chunks": 0,
                "total_embeddings": 0,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            raise RuntimeError(f"Failed to create PDF directory {pdf_dir}: {str(e)}")
    
    # Check if directory has PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return {
            "status": "no_pdfs",
            "message": f"No PDF files found in {pdf_dir}. Please add PDF files and run again.",
            "total_pdfs": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    # Initialize components
    pdf_processor = create_pdf_processor(chunk_size, chunk_overlap)
    embeddings_generator = EmbeddingsGenerator()
    vector_db = create_supabase_indexer()
    
    logger.info(f"Processing PDF files in {pdf_dir}")
    start_time = time.time()
    
    # Process PDF directory
    processed_docs = pdf_processor.process_dir(pdf_dir)
    
    # Initialize counters
    total_pdfs = len(processed_docs)
    total_chunks = 0
    total_embeddings = 0
    total_failures = 0
    error_count = 0
    
    # Process each document
    for doc in processed_docs:
        try:
            # Skip documents with errors
            if "error" in doc:
                logger.warning(f"Skipping document with error: {doc.get('filename', 'unknown')}")
                error_count += 1
                continue
            
            # Get chunks
            chunks = doc.get("chunks", [])
            total_chunks += len(chunks)
            
            if not chunks:
                logger.warning(f"No chunks found in document: {doc.get('filename', 'unknown')}")
                continue
            
            # Generate embeddings for chunks with partial result handling
            try:
                # Process all chunks at once with partial result support
                embedding_results = embeddings_generator.generate_embeddings_with_partial_results(chunks)
                
                successful_embeddings = embedding_results["embeddings"]
                failed_chunks = embedding_results["failed_texts"]
                
                # Log success and failure information
                if embedding_results["failure_count"] > 0:
                    logger.warning(
                        f"Document {doc.get('filename', 'unknown')}: "
                        f"{embedding_results['success_count']} chunks embedded successfully, "
                        f"{embedding_results['failure_count']} chunks failed due to rate limits"
                    )
                
                # Create document records for successfully embedded chunks
                embedded_docs = []
                for i, (chunk, embedding) in enumerate(zip(chunks[:len(successful_embeddings)], successful_embeddings)):
                    # Validate the embedding vector before adding to the batch
                    if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                        logger.warning(f"Skipping chunk {i} due to invalid embedding (empty or null)")
                        continue
                    
                    # Log embedding dimension for debugging
                    if i == 0:  # Only log for the first embedding to avoid spam
                        logger.info(f"First embedding dimension: {len(embedding)}")
                    
                    embedded_doc = {
                        "id": f"{doc.get('id', 'doc')}_{i}",
                        "text": chunk,
                        "embedding": embedding,
                        "metadata": {
                            "filename": doc.get("filename", ""),
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    }
                    embedded_docs.append(embedded_doc)
                
                # Index document embeddings if we have any successful ones
                if embedded_docs:
                    indexed_count = vector_db.index_documents(embedded_docs)
                    total_embeddings += indexed_count
                    
                    if indexed_count == 0:
                        logger.warning(f"Failed to index any chunks for {doc.get('filename', 'document')} - check vector dimensions")
                    else:
                        logger.info(
                            f"Partially processed {doc.get('filename', 'document')}: "
                            f"{indexed_count}/{len(embedded_docs)} chunks indexed into Supabase"
                        )
                
                # Store information about failed chunks if needed
                if failed_chunks:
                    # Here you could implement storing metadata about failed chunks
                    # for later retry or tracking purposes
                    failed_chunk_count = len(failed_chunks)
                    total_failures += failed_chunk_count
                    logger.warning(
                        f"Rate limit encountered - {failed_chunk_count} chunks from "
                        f"{doc.get('filename', 'unknown')} could not be embedded"
                    )
                
            except Exception as e:
                logger.error(f"Error embedding document {doc.get('filename', 'unknown')}: {str(e)}")
                error_count += 1
            
        except Exception as e:
            logger.error(f"Error processing document {doc.get('filename', 'unknown')}: {str(e)}")
            error_count += 1
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Return processing stats
    return {
        "total_pdfs": len(processed_docs),
        "total_chunks": total_chunks,
        "indexed_chunks": total_embeddings,
        "failed_chunks": total_failures,
        "errors": error_count,
        "processing_time_seconds": processing_time
    }

def search(
    query: str,
    top_k: int = 5,
    alpha: float = 0.5,
    use_rag: bool = False,
    rag_mode: str = "summarize",
    model: str = "gpt-3.5-turbo",
    output_file: Optional[str] = None,
    no_raw: bool = False
) -> Dict[str, Any]:
    """
    Search for content semantically related to the query.
    
    This function performs semantic search using vector embeddings. It can
    optionally enhance the search results using RAG (Retrieval-Augmented Generation).
    
    Args:
        query: Search query
        top_k: Number of results to return
        alpha: Weight for hybrid search (1.0 = semantic only)
        use_rag: Whether to use RAG to enhance results
        rag_mode: RAG processing mode (summarize, analyze, explain, detail, person)
        model: OpenAI model to use for RAG
        output_file: File to save results to
        no_raw: Whether to hide raw search results in output
        
    Returns:
        Dictionary with search results
    """
    # Initialize components
    embeddings_generator = EmbeddingsGenerator()
    vector_db = create_supabase_indexer()
    query_engine = QueryEngine(embeddings_generator, vector_db)
    
    # Use a simple regex-based approach to check if this is a person query
    is_person_query = query_engine.is_person_query(query)
    person_name = None
    
    if is_person_query:
        person_name = query_engine.extract_person_name(query)
        logger.info(f"Detected person query for: {person_name or 'unknown person'}")
        # Auto-set RAG mode to "person" for person queries
        if use_rag:
            rag_mode = "person"
            logger.info("Auto-setting RAG mode to 'person'")
    
    # Perform search
    start_time = time.time()
    search_results = query_engine.search(query, top_k=top_k, alpha=alpha)
    search_time = time.time() - start_time
    
    # Prepare result object
    result = {
        "query": query,
        "results_count": len(search_results),
        "search_time": search_time,
        "timestamp": datetime.datetime.now().isoformat(),
        "is_person_query": is_person_query,
        "person_name": person_name
    }
    
    # Add raw results if requested
    if not no_raw:
        result["results"] = search_results
    
    # Apply RAG if requested
    if use_rag and search_results:
        try:
            # Initialize OpenAI processor
            openai_processor = OpenAIProcessor(model=model)
            
            # Process results with RAG
            rag_start_time = time.time()
            rag_result = openai_processor.summarize_search_results(
                query=query,
                search_results=search_results,
                mode=rag_mode
            )
            rag_time = time.time() - rag_start_time
            
            # Add RAG results to output
            result["rag_result"] = rag_result.get("processed_result", "")
            result["rag_time"] = rag_time
            result["rag_mode"] = rag_mode
            result["rag_model"] = model
            
        except Exception as e:
            logger.error(f"Error processing results with RAG: {str(e)}")
            result["rag_error"] = str(e)
    
    # Save results to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results to file: {str(e)}")
    
    return result

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="PDF Vector Search Engine")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process PDF files")
    process_parser.add_argument("--pdf-dir", type=str, required=True, help="Directory containing PDF files")
    process_parser.add_argument("--chunk-size", type=int, default=500, help="Maximum chunk size")
    process_parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    process_parser.add_argument("--force", action="store_true", help="Force reprocessing of files")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for content")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    search_parser.add_argument("--alpha", type=float, default=0.5, help="Weight for hybrid search (1.0 = semantic only)")
    search_parser.add_argument("--rag", action="store_true", help="Use RAG to enhance results")
    search_parser.add_argument("--rag-mode", type=str, default="summarize", 
                               choices=["summarize", "analyze", "explain", "detail", "person"],
                               help="RAG processing mode")
    search_parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="OpenAI model for RAG")
    search_parser.add_argument("--output", type=str, help="File to save results to")
    search_parser.add_argument("--no-raw", action="store_true", help="Hide raw search results in output")
    
    return parser.parse_args()

def main():
    """
    Main entry point for the application.
    """
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Parse command-line arguments
    args = parse_args()
    
    try:
        if args.command == "process":
            # Process PDF files
            result = process_pdfs(
                pdf_dir=args.pdf_dir,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                force=args.force
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == "search":
            # Search for content
            result = search(
                query=args.query,
                top_k=args.top_k,
                alpha=args.alpha,
                use_rag=args.rag,
                rag_mode=args.rag_mode,
                model=args.model,
                output_file=args.output,
                no_raw=args.no_raw
            )
            
            # Print search results
            print(f"\nSearch results for: '{args.query}'")
            print(f"Found {result['results_count']} results")
            
            if result['results_count'] == 0:
                print("No results found for your query.")
            else:
                # Print raw results if requested
                if not args.no_raw and "results" in result:
                    print("\nRaw Search Results:")
                    for i, res in enumerate(result["results"]):
                        print(f"\nResult {i+1} (Score: {res['score']:.4f})")
                        print(f"File: {res['metadata'].get('filename', 'Unknown')}")
                        print(f"Text: {res['text'][:200]}...")
                
                # Print RAG results if available
                if "rag_result" in result:
                    print("\nEnhanced Results:")
                    print(result["rag_result"])
            
        else:
            print("Please specify a command: process or search")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
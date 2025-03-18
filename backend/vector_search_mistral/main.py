"""
Main script for PDF processing and indexing.
This script coordinates the entire PDF processing pipeline:
1. Extract text from PDFs using Mistral OCR
2. Preprocess and chunk the text
3. Generate embeddings
4. Index the embeddings in Pinecone
"""

import os
import argparse
import logging
import time
import sys
import traceback
import glob
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Use absolute imports instead of relative imports
from backend.vector_search_mistral.pdf_processor import MistralPDFProcessor
from backend.vector_search_mistral.text_preprocessor import TextPreprocessor
from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
from backend.vector_search_mistral.pinecone_indexer import PineconeIndexer
from backend.vector_search_mistral.query_engine import QueryEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def process_and_index_pdfs(
    pdf_dir: str = "pdf_data/raw-files",
    chunk_size: int = 512,
    chunk_overlap: int = 128,
    force_reprocess: bool = False,
    mistral_api_key: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    pinecone_region: Optional[str] = None,
    index_name: str = "pdf-embeddings"
) -> Dict[str, Any]:
    """
    Process PDF files, extract text, create embeddings, and index them in Pinecone.
    
    Args:
        pdf_dir: Directory containing PDF files
        chunk_size: Max size of text chunks in characters
        chunk_overlap: Overlap between consecutive chunks in characters
        force_reprocess: Force reprocessing of all PDFs
        mistral_api_key: Mistral API key (defaults to env var)
        pinecone_api_key: Pinecone API key (defaults to env var)
        pinecone_region: Pinecone environment region (defaults to env var)
        index_name: Name of the Pinecone index
        
    Returns:
        Dictionary with processing statistics
    """
    start_time = time.time()
    
    # Get API keys from environment variables if not provided
    mistral_api_key = mistral_api_key or os.environ.get("MISTRAL_API_KEY")
    pinecone_api_key = pinecone_api_key or os.environ.get("PINECONE_API_KEY")
    pinecone_region = pinecone_region or os.environ.get("PINECONE_REGION")
    
    # Check if required API keys are available
    if not mistral_api_key:
        logger.warning("Mistral API key not provided and not found in environment variables")
    
    if not pinecone_api_key or not pinecone_region:
        logger.error("Pinecone API key and region are required")
        return {
            "status": "error",
            "message": "Pinecone API key and region are required",
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_indexed": 0,
            "errors": 1,
            "processing_time": 0
        }
    
    # Initialize components
    try:
        pdf_processor = MistralPDFProcessor(mistral_api_key=mistral_api_key)
        text_preprocessor = TextPreprocessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        embeddings_generator = EmbeddingsGenerator(api_key=mistral_api_key)
        indexer = PineconeIndexer(
            api_key=pinecone_api_key,
            environment=pinecone_region,
            index_name=index_name
        )
        
        logger.info(f"Initialized all components for processing PDFs from {pdf_dir}")
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return {
            "status": "error",
            "message": f"Error initializing components: {str(e)}",
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_indexed": 0,
            "errors": 1,
            "processing_time": 0
        }
    
    # Create PDF directory if it doesn't exist
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Get list of PDF files
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir}")
        return {
            "status": "warning",
            "message": f"No PDF files found in {pdf_dir}",
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_indexed": 0,
            "errors": 0,
            "processing_time": time.time() - start_time
        }
    
    # Process each PDF file
    stats = {
        "pdfs_processed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "vectors_indexed": 0,
        "errors": 0
    }
    
    for pdf_file in pdf_files:
        try:
            pdf_path = Path(pdf_file)
            logger.info(f"Processing PDF: {pdf_path.name}")
            
            # Extract text from PDF
            extracted_text = pdf_processor.extract_text(str(pdf_path))
            
            # Split text into chunks
            chunks = text_preprocessor.process_text(extracted_text)
            stats["chunks_created"] += len(chunks)
            
            # Generate embeddings for chunks
            embedded_docs = embeddings_generator.generate_embeddings({
                "id": pdf_path.stem,
                "text": extracted_text,
                "chunks": chunks,
                "metadata": {
                    "filename": pdf_path.name,
                    "path": str(pdf_path),
                    "chunk_count": len(chunks)
                }
            })
            
            # Index embeddings in Pinecone
            if embedded_docs:
                indexer.index_documents(embedded_docs)
                stats["vectors_indexed"] += len(embedded_docs)
                stats["embeddings_generated"] += len(embedded_docs)
                stats["pdfs_processed"] += 1
                logger.info(f"Successfully processed and indexed {pdf_path.name} with {len(chunks)} chunks")
            else:
                logger.error(f"Failed to generate embeddings for {pdf_path.name}")
                stats["errors"] += 1
            
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {str(e)}")
            stats["errors"] += 1
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Return processing statistics
    result = {
        "status": "success" if stats["errors"] == 0 else "partial_success",
        "message": f"Processed {stats['pdfs_processed']} PDFs in {processing_time:.2f} seconds",
        "processing_time": processing_time,
        **stats
    }
    
    logger.info(f"Processing complete: {result['message']}")
    return result


def search_pdfs(
    query: str,
    top_k: int = 5,
    alpha: float = 0.5,
    mistral_api_key: Optional[str] = None,
    pinecone_api_key: Optional[str] = None,
    pinecone_region: Optional[str] = None,
    index_name: str = "pdf-embeddings"
) -> List[Dict[str, Any]]:
    """
    Search for PDFs using hybrid search.
    
    Args:
        query: Search query
        top_k: Number of results to return
        alpha: Weight for hybrid search (0 = BM25, 1 = vector)
        mistral_api_key: Mistral API key (defaults to env var)
        pinecone_api_key: Pinecone API key (defaults to env var)
        pinecone_region: Pinecone environment region (defaults to env var)
        index_name: Name of the Pinecone index
        
    Returns:
        List of search results with metadata
    """
    try:
        query_engine = QueryEngine(
            index_name=index_name,
            mistral_api_key=mistral_api_key,
            pinecone_api_key=pinecone_api_key,
            pinecone_region=pinecone_region
        )
        
        results = query_engine.search(query=query, top_k=top_k, alpha=alpha)
        
        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        return []


def main():
    """Main function to run PDF processing and search."""
    parser = argparse.ArgumentParser(description="Process and search PDF documents")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process and index PDF files")
    process_parser.add_argument("--pdf-dir", type=str, default="pdf_data/raw-files", 
                              help="Directory containing PDF files")
    process_parser.add_argument("--chunk-size", type=int, default=512, 
                              help="Maximum size of text chunks in characters")
    process_parser.add_argument("--chunk-overlap", type=int, default=128, 
                              help="Overlap between consecutive chunks in characters")
    process_parser.add_argument("--force", action="store_true", 
                              help="Force reprocessing of all PDFs")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search PDF documents")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, 
                             help="Number of results to return")
    search_parser.add_argument("--alpha", type=float, default=0.5, 
                             help="Weight for hybrid search (0 = sparse only, 1 = dense only)")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "process":
        # Process and index PDFs
        result = process_and_index_pdfs(
            pdf_dir=args.pdf_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force_reprocess=args.force
        )
        
        print("\nProcessing Summary:")
        print(f"Total PDFs processed: {result['pdfs_processed']}")
        print(f"Chunks created: {result['chunks_created']}")
        print(f"Embeddings generated: {result['embeddings_generated']}")
        print(f"Vectors indexed: {result['vectors_indexed']}")
        print(f"Errors: {result['errors']}")
        
    elif args.command == "search":
        # Search PDFs
        results = search_pdfs(
            query=args.query,
            top_k=args.top_k,
            alpha=args.alpha
        )
        
        print(f"\nSearch results for: '{args.query}'")
        print(f"Found {len(results)} matching documents\n")
        
        for i, result in enumerate(results):
            print(f"Document {i+1}: {result['metadata']['filename']}")
            print(f"Score: {result['score']}")
            print(f"Text: {result['text'][:200]}...")
            print()
    
    else:
        # No command provided, show help
        parser.print_help()


if __name__ == "__main__":
    main() 
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
from typing import List, Dict, Any
from dotenv import load_dotenv

from pdf_processor import MistralPDFProcessor
from text_preprocessor import TextPreprocessor
from embeddings_generator import EmbeddingsGenerator
from pinecone_indexer import PineconeIndexer
from query_engine import QueryEngine

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def process_and_index_pdfs(pdf_dir: str = "pdf_data/raw-files",
                          chunk_size: int = 512,
                          chunk_overlap: int = 128,
                          force_reprocess: bool = False) -> Dict[str, Any]:
    """
    Process PDF files and index them in Pinecone.
    
    Args:
        pdf_dir: Directory containing PDF files
        chunk_size: Maximum size of text chunks in characters
        chunk_overlap: Overlap between consecutive chunks in characters
        force_reprocess: Whether to reprocess PDFs that have already been indexed
        
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Starting PDF processing pipeline with directory: {pdf_dir}")
    start_time = time.time()
    
    # Initialize components
    pdf_processor = MistralPDFProcessor()
    text_preprocessor = TextPreprocessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embedding_generator = EmbeddingsGenerator()
    pinecone_indexer = PineconeIndexer(index_name="pdf-data-vector")
    
    # Get current index stats
    index_stats = pinecone_indexer.get_stats()
    logger.info(f"Current index stats: {index_stats}")
    
    # Step 1: Process PDFs with OCR
    logger.info("Step 1: Processing PDFs with OCR...")
    processed_pdfs = pdf_processor.process_pdf_directory(pdf_dir)
    logger.info(f"Processed {len(processed_pdfs)} PDF files")
    
    # For already processed files, check if we should skip them
    if not force_reprocess:
        # Get list of filenames currently in the index
        existing_filenames = set()
        try:
            # This is a simplification; in reality, you'd need to query for all filenames
            # which could require multiple queries if there are many documents
            if 'namespaces' in index_stats and 'pdf-data-vector' in index_stats['namespaces']:
                existing_count = index_stats['namespaces']['pdf-data-vector']['vector_count']
                logger.info(f"Index already contains {existing_count} vectors")
        except Exception as e:
            logger.warning(f"Could not get existing filenames: {str(e)}")
    
    stats = {
        "total_pdfs": len(processed_pdfs),
        "chunks_created": 0,
        "embeddings_generated": 0,
        "vectors_indexed": 0,
        "errors": 0
    }
    
    # Process each PDF
    for pdf_data in processed_pdfs:
        filename = pdf_data.get("filename")
        logger.info(f"Processing PDF: {filename}")
        
        try:
            # Step 2: Preprocess and chunk text
            chunks = text_preprocessor.preprocess_document(pdf_data)
            stats["chunks_created"] += len(chunks)
            logger.info(f"Created {len(chunks)} chunks for {filename}")
            
            # Step 3: Generate embeddings
            chunk_embeddings = embedding_generator.generate_hybrid_embeddings(chunks)
            stats["embeddings_generated"] += len(chunk_embeddings)
            logger.info(f"Generated embeddings for {len(chunk_embeddings)} chunks")
            
            # Step 4: Index in Pinecone
            index_result = pinecone_indexer.index_embeddings(chunk_embeddings)
            stats["vectors_indexed"] += index_result.get("indexed", 0)
            stats["errors"] += index_result.get("errors", 0)
            logger.info(f"Indexed {index_result.get('indexed', 0)} vectors with {index_result.get('errors', 0)} errors")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            stats["errors"] += 1
    
    # Calculate processing time
    elapsed_time = time.time() - start_time
    stats["processing_time_seconds"] = elapsed_time
    
    logger.info(f"PDF processing pipeline completed in {elapsed_time:.2f} seconds")
    logger.info(f"Final stats: {stats}")
    
    # Get updated index stats
    final_index_stats = pinecone_indexer.get_stats()
    logger.info(f"Final index stats: {final_index_stats}")
    
    return stats


def search_pdfs(query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict]:
    """
    Search PDF documents with a query.
    
    Args:
        query: User query
        top_k: Number of results to return
        alpha: Weight for hybrid search (0 = sparse only, 1 = dense only)
        
    Returns:
        List of search results
    """
    logger.info(f"Searching PDFs with query: '{query}'")
    
    # Initialize query engine
    query_engine = QueryEngine(index_name="pdf-data-vector")
    
    # Execute search
    results = query_engine.search(query, top_k=top_k, alpha=alpha)
    
    return results


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
        stats = process_and_index_pdfs(
            pdf_dir=args.pdf_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force_reprocess=args.force
        )
        
        print("\nProcessing Summary:")
        print(f"Total PDFs processed: {stats['total_pdfs']}")
        print(f"Chunks created: {stats['chunks_created']}")
        print(f"Embeddings generated: {stats['embeddings_generated']}")
        print(f"Vectors indexed: {stats['vectors_indexed']}")
        print(f"Errors: {stats['errors']}")
        print(f"Processing time: {stats['processing_time_seconds']:.2f} seconds")
        
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
            print(f"Document {i+1}: {result['filename']}")
            print(f"Score: {result['score']}")
            print(f"Matches:")
            
            for j, match in enumerate(result['text_matches'][:2]):  # Show up to 2 matches
                print(f"  {j+1}. {match['text'][:200]}...")
            
            if len(result['text_matches']) > 2:
                print(f"  ... and {len(result['text_matches']) - 2} more matches")
            
            print()
    
    else:
        # No command provided, show help
        parser.print_help()


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Standalone run script for PDF processing and search.
This script is designed to be executed directly.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import our modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def setup_args_parser():
    """Set up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="PDF Vector Search and Processing Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process and index PDF files")
    process_parser.add_argument("--pdf-dir", default="pdf_data/raw-files", help="Directory containing PDF files")
    process_parser.add_argument("--chunk-size", type=int, default=512, help="Maximum size of text chunks in characters")
    process_parser.add_argument("--chunk-overlap", type=int, default=128, help="Overlap between consecutive chunks in characters")
    process_parser.add_argument("--force", action="store_true", help="Force reprocessing of all PDFs")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    search_parser.add_argument("--alpha", type=float, default=0.5, help="Weight for hybrid search (0=sparse only, 1=dense only)")
    search_parser.add_argument("--rag", action="store_true", help="Enable RAG processing with OpenAI")
    search_parser.add_argument("--rag-mode", choices=["summarize", "analyze", "explain", "detail"], default="summarize", 
                               help="RAG processing mode when --rag is enabled")
    search_parser.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model to use for RAG")
    
    return parser

def check_environment():
    """Check for required environment variables."""
    # Load .env file if it exists
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Using .env file from: {env_path}")
    
    # Check for required environment variables
    required_vars = ["MISTRAL_API_KEY", "PINECONE_API_KEY", "PINECONE_REGION"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file or your environment.")
        sys.exit(1)
    else:
        print("\n✅ All required environment variables are set!")

def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = setup_args_parser()
    args = parser.parse_args()
    
    # Check for required environment variables
    check_environment()
    
    # Import modules here to avoid loading them if environment check fails
    try:
        from backend.vector_search_mistral.main import process_and_index_pdfs, search_pdfs
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        logger.error("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Process command
    if args.command == "process":
        # Print processing parameters
        print(f"Processing PDFs in directory: {args.pdf_dir}")
        print(f"Chunk size: {args.chunk_size}, Chunk overlap: {args.chunk_overlap}")
        
        # Process and index PDFs
        result = process_and_index_pdfs(
            pdf_dir=args.pdf_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force_reprocess=args.force
        )
        
        # Print results
        print("\n--- Processing Summary ---")
        if result.get("status") == "error":
            print(f"Error processing PDFs: {result.get('message')}")
        else:
            print(f"Total PDFs processed: {result['pdfs_processed']}")
            print(f"Chunks created: {result['chunks_created']}")
            print(f"Embeddings generated: {result['embeddings_generated']}")
            print(f"Vectors indexed: {result['vectors_indexed']}")
            print(f"Errors: {result['errors']}")
            print(f"Processing time: {result['processing_time']:.2f} seconds")
    
    # Search command
    elif args.command == "search":
        print(f"Searching for: {args.query}")
        print(f"Top-k results: {args.top_k}, Alpha: {args.alpha}")
        
        # Search for documents
        results = search_pdfs(
            query=args.query,
            top_k=args.top_k,
            alpha=args.alpha
        )
        
        # Print results count
        print(f"\nFound {len(results)} results:")
        
        if not results:
            print("No matching documents found.")
        
        # Apply RAG processing if enabled
        if args.rag and results:
            try:
                from backend.vector_search_mistral.openai_processor import process_rag_results
                
                if not os.environ.get("OPENAI_API_KEY"):
                    print("\n⚠️ Warning: OPENAI_API_KEY not set in environment. RAG processing may fail.")
                
                print(f"\n--- RAG Processing ({args.rag_mode}) ---")
                rag_result = process_rag_results(
                    query=args.query,
                    search_results=results,
                    mode=args.rag_mode,
                    model=args.model
                )
                
                if "error" in rag_result:
                    print(f"Error: {rag_result['error']}")
                else:
                    print("\n" + rag_result["processed_result"])
                
                # Also print raw results in condensed format
                print("\n--- Raw Search Results ---")
                for i, result in enumerate(results):
                    print(f"[{i+1}] {result['metadata']['filename']} (Score: {result['score']:.4f})")
                
            except Exception as e:
                logger.error(f"Error in RAG processing: {str(e)}")
                print(f"\nError processing with OpenAI: {str(e)}")
                
                # Fall back to showing regular results
                for i, result in enumerate(results):
                    print(f"Result #{i+1}")
                    print(f"Document: {result['metadata']['filename']}")
                    print(f"Score: {result['score']:.4f}")
                    print(f"Text: {result['text'][:200]}..." if len(result['text']) > 200 else result['text'])
                    print()
        else:
            # Show regular results
            for i, result in enumerate(results):
                print(f"Result #{i+1}")
                print(f"Document: {result['metadata']['filename']}")
                print(f"Score: {result['score']:.4f}")
                print(f"Text: {result['text'][:200]}..." if len(result['text']) > 200 else result['text'])
                print()
    
    # No command specified
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
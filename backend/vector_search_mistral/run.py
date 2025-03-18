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
    search_parser.add_argument("--rag-mode", choices=["summarize", "analyze", "explain", "detail", "person"], 
                               default="summarize", help="RAG processing mode when --rag is enabled")
    search_parser.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model to use for RAG")
    search_parser.add_argument("--no-raw", action="store_true", help="Hide raw search results when using RAG")
    
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

def format_search_results(results: List[Dict[str, Any]], detailed: bool = False) -> str:
    """Format search results for display."""
    if not results:
        return "No matching documents found."
    
    output = []
    for i, result in enumerate(results):
        output.append(f"Result #{i+1}")
        output.append(f"Document: {result['metadata']['filename']}")
        output.append(f"Score: {result['score']:.4f}")
        
        if detailed:
            output.append(f"Text: {result['text']}")
        else:
            text = result['text']
            if len(text) > 200:
                text = text[:200] + "..."
            output.append(f"Text: {text}")
        
        output.append("")
    
    return "\n".join(output)

def format_condensed_results(results: List[Dict[str, Any]]) -> str:
    """Format search results in a condensed format."""
    if not results:
        return "No matching documents found."
    
    output = []
    for i, result in enumerate(results):
        output.append(f"[{i+1}] {result['metadata']['filename']} (Score: {result['score']:.4f})")
    
    return "\n".join(output)

def is_person_query(query: str) -> bool:
    """Simple check if this is a person query."""
    person_keywords = [
        "who is", "worked on", "projects by", "person", "employee", 
        "staff", "personnel", "team member", "colleague", "manager",
        "engineer", "supervisor", "lead", "director", "worked with"
    ]
    
    lower_query = query.lower()
    return any(keyword in lower_query for keyword in person_keywords)

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
        # Detect if this is a person query and adjust mode
        if is_person_query(args.query) and args.rag and args.rag_mode == "summarize":
            args.rag_mode = "person"
            logger.info(f"Auto-detected person query. Using '{args.rag_mode}' mode.")
        
        print(f"Searching for: {args.query}")
        print(f"Top-k results: {args.top_k}, Alpha: {args.alpha}")
        if args.rag:
            print(f"RAG mode: {args.rag_mode}")
        
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
            return
        
        # Apply RAG processing if enabled
        if args.rag and results:
            try:
                from backend.vector_search_mistral.openai_processor import process_rag_results
                
                if not os.environ.get("OPENAI_API_KEY"):
                    print("\n⚠️ Warning: OPENAI_API_KEY not set in environment. RAG processing may fail.")
                
                # If person mode, use a more descriptive header
                if args.rag_mode == "person":
                    # Extract the person name from the query (simple method)
                    words = args.query.split()
                    name = "the person"
                    
                    for i in range(len(words) - 1):
                        if words[i][0].isupper() and words[i+1][0].isupper():
                            name = f"{words[i]} {words[i+1]}"
                            break
                    
                    print(f"\n--- Projects and Information for {name} ---")
                else:
                    print(f"\n--- RAG Processing ({args.rag_mode}) ---")
                
                # Process with OpenAI
                rag_result = process_rag_results(
                    query=args.query,
                    search_results=results,
                    mode=args.rag_mode,
                    model=args.model
                )
                
                if "error" in rag_result:
                    print(f"Error: {rag_result['error']}")
                else:
                    # Get the person name if available
                    person_name = rag_result.get("person_name")
                    if person_name and args.rag_mode == "person":
                        print(f"\n--- Information for {person_name} ---")
                    
                    # Print the processed result
                    print("\n" + rag_result["processed_result"])
                
                # Also print raw results if requested
                if not args.no_raw:
                    print("\n--- Source Documents ---")
                    print(format_condensed_results(results))
                    print("\nUse the --no-raw flag to hide source documents.")
                
            except Exception as e:
                logger.error(f"Error in RAG processing: {str(e)}")
                print(f"\nError processing with OpenAI: {str(e)}")
                
                # Fall back to showing regular results
                print(format_search_results(results))
        else:
            # Show regular results
            print(format_search_results(results))
    
    # No command specified
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 
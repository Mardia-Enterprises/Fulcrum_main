#!/usr/bin/env python3
"""
PDF Vector Search Engine - Main Execution Script
-------------------------------------------------------------------------------
This production-ready script provides the command-line interface for processing
PDF documents and performing vector searches with optional RAG enhancements.
It supports two main operations:
1. Processing PDF files for vector indexing
2. Searching indexed documents with various modes and options

For production deployment, this script can be executed directly or via a service
manager like systemd, supervisor, or docker.
"""

import os
import sys
import argparse
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add module path handling for production deployment
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Set up logging with timestamp format
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)
logger = logging.getLogger("pdf_search")

# Optional: Configure file logging for production
# file_handler = logging.FileHandler('pdf_search.log')
# file_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(file_handler)

def setup_args_parser() -> argparse.ArgumentParser:
    """
    Configure command-line argument parser with all supported options.
    
    Returns:
        A configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="PDF Vector Search Engine",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process and index PDF files")
    process_parser.add_argument("--pdf-dir", default="pdf_data/raw-files", 
                              help="Directory containing PDF files")
    process_parser.add_argument("--chunk-size", type=int, default=512, 
                              help="Maximum size of text chunks in characters")
    process_parser.add_argument("--chunk-overlap", type=int, default=128, 
                              help="Overlap between consecutive chunks in characters")
    process_parser.add_argument("--force", action="store_true", 
                              help="Force reprocessing of all PDFs")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, 
                             help="Number of results to return")
    search_parser.add_argument("--alpha", type=float, default=0.5, 
                             help="Weight for hybrid search (0=sparse only, 1=dense only)")
    search_parser.add_argument("--rag", action="store_true", 
                             help="Enable RAG processing with OpenAI")
    search_parser.add_argument("--rag-mode", 
                             choices=["summarize", "analyze", "explain", "detail", "person"], 
                             default="summarize", 
                             help="RAG processing mode when --rag is enabled")
    search_parser.add_argument("--model", default="gpt-3.5-turbo", 
                             help="OpenAI model to use for RAG")
    search_parser.add_argument("--no-raw", action="store_true", 
                             help="Hide raw search results when using RAG")
    search_parser.add_argument("--output", 
                             help="Output file to save results (optional)")
    
    return parser

def check_environment() -> bool:
    """
    Verify that required environment variables are properly set.
    
    Returns:
        bool: True if all required variables are set, False otherwise.
    """
    # Load environment variables from env file if available
    try:
        from dotenv import load_dotenv
        # Look for .env file in script directory first, then current directory
        env_paths = [
            os.path.join(script_dir, ".env"),
            os.path.join(os.getcwd(), ".env")
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                break
    except ImportError:
        logger.warning("python-dotenv not installed. Using existing environment variables.")
    
    # Check for required environment variables
    required_vars = ["MISTRAL_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in the environment or .env file.")
        return False
    
    # Check for optional variables
    optional_vars = ["OPENAI_API_KEY", "PINECONE_INDEX_NAME", "MISTRAL_MODEL", "OPENAI_MODEL"]
    for var in optional_vars:
        if not os.environ.get(var):
            if var == "OPENAI_API_KEY":
                logger.warning(f"{var} not set. RAG features will not be available.")
            else:
                logger.info(f"{var} not set. Using default value.")
    
    logger.info("Environment check passed. Required variables are set.")
    return True

def format_search_results(results: List[Dict[str, Any]], detailed: bool = False) -> str:
    """
    Format search results for display or output.
    
    Args:
        results: List of search result dictionaries
        detailed: Whether to show full text or truncated excerpts
        
    Returns:
        Formatted string of search results
    """
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
    """
    Format search results in a compact format for display.
    
    Args:
        results: List of search result dictionaries
        
    Returns:
        Condensed string representation of results
    """
    if not results:
        return "No matching documents found."
    
    output = []
    for i, result in enumerate(results):
        output.append(f"[{i+1}] {result['metadata']['filename']} (Score: {result['score']:.4f})")
    
    return "\n".join(output)

def is_person_query(query: str) -> bool:
    """
    Determine if a query is asking about a specific person.
    
    Args:
        query: The search query string
        
    Returns:
        True if the query appears to be about a person, False otherwise
    """
    person_keywords = [
        "who is", "worked on", "projects by", "person", "employee", 
        "staff", "personnel", "team member", "colleague", "manager",
        "engineer", "supervisor", "lead", "director", "worked with"
    ]
    
    lower_query = query.lower()
    return any(keyword in lower_query for keyword in person_keywords)

def save_to_file(content: str, filename: str) -> None:
    """
    Save search results to a file.
    
    Args:
        content: Content to write to file
        filename: Path to output file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results to {filename}: {str(e)}")

def process_command(args) -> int:
    """
    Handle the 'process' command to index PDF documents.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        from main import process_pdfs
        
        # Validate input directory
        pdf_dir = os.path.abspath(args.pdf_dir)
        if not os.path.exists(pdf_dir):
            logger.error(f"PDF directory does not exist: {pdf_dir}")
            return 1
        
        logger.info(f"Processing PDFs in directory: {pdf_dir}")
        logger.info(f"Chunk size: {args.chunk_size}, Chunk overlap: {args.chunk_overlap}")
        
        # Record start time for performance tracking
        start_time = datetime.now()
        
        # Process and index PDFs
        result = process_pdfs(
            pdf_dir=pdf_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force=args.force
        )
        
        # Record end time
        processing_time = datetime.now() - start_time
        
        # Print results
        print("\n--- Processing Summary ---")
        print(f"Total PDFs processed: {result['total_pdfs']}")
        print(f"Chunks created: {result['total_chunks']}")
        print(f"Embeddings generated: {result['total_embeddings']}")
        print(f"Errors: {result['error_count']}")
        print(f"Processing time: {processing_time.total_seconds():.2f} seconds")
            
        logger.info(f"Processing completed: {result['total_pdfs']} PDFs, "
                    f"{result['total_chunks']} chunks, "
                    f"{result['total_embeddings']} embeddings, "
                    f"{result['error_count']} errors")
        return 0
    
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        print(f"Error: Could not import necessary modules: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        logger.debug(traceback.format_exc())
        print(f"Error processing PDFs: {str(e)}")
        return 1

def search_command(args) -> int:
    """
    Handle the 'search' command to search indexed documents.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        from main import search
        
        # Validate inputs
        if args.alpha < 0 or args.alpha > 1:
            logger.error(f"Alpha must be between 0 and 1, got {args.alpha}")
            print(f"Error: Alpha must be between 0 and 1, got {args.alpha}")
            return 1
        
        # Auto-detect person queries
        if is_person_query(args.query) and args.rag and args.rag_mode == "summarize":
            args.rag_mode = "person"
            logger.info(f"Auto-detected person query. Using '{args.rag_mode}' mode.")
        
        # Log search parameters
        logger.info(f"Searching for: '{args.query}'")
        logger.info(f"Search parameters: top_k={args.top_k}, alpha={args.alpha}")
        if args.rag:
            logger.info(f"RAG mode: {args.rag_mode}, model: {args.model}")
        
        # Print search parameters
        print(f"Searching for: {args.query}")
        print(f"Top-k results: {args.top_k}, Alpha: {args.alpha}")
        if args.rag:
            print(f"RAG mode: {args.rag_mode}")
        
        # Record start time
        start_time = datetime.now()
        
        # Perform search
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
        
        # Record search time
        search_time = datetime.now() - start_time
        logger.info(f"Search completed in {search_time.total_seconds():.2f} seconds, found {result['results_count']} results")
        
        # Print results count
        print(f"\nFound {result['results_count']} results")
        
        if result['results_count'] == 0:
            print("No results found for your query.")
            return 0
            
        # Print raw results if requested and available
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
            
        return 0
        
    except ImportError as e:
        logger.error(f"Error importing required modules: {str(e)}")
        print(f"Error: Could not import necessary modules: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        logger.debug(traceback.format_exc())
        print(f"Error performing search: {str(e)}")
        return 1

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse command-line arguments
    parser = setup_args_parser()
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1
    
    # Check environment variables
    if not check_environment():
        return 1
    
    # Execute the appropriate command
    if args.command == "process":
        return process_command(args)
    elif args.command == "search":
        return search_command(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        logger.info("Operation cancelled by user.")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        logger.critical(f"Unhandled error: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1) 
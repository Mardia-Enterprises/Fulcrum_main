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
import time

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

def load_root_env_vars():
    try:
        from dotenv import load_dotenv
        
        # Get the path to the root .env file
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        env_path = os.path.join(root_dir, ".env")
        
        # Load environment variables
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment variables from {env_path}")
            return True
        else:
            logger.warning(f"Root .env file not found at {env_path}. Using system environment variables.")
            return False
    except ImportError:
        logger.warning("python-dotenv not installed. Using system environment variables.")
        return False

def check_env_vars(args=None):
    required_vars = ["MISTRAL_API_KEY", "SUPABASE_PROJECT_URL", "SUPABASE_PRIVATE_API_KEY"]
    
    # Check if OpenAI API key is set when RAG is enabled
    if args and hasattr(args, 'rag') and args.rag and hasattr(args, "command") and args.command == "search":
        required_vars.append("OPENAI_API_KEY")
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in the root .env file")
        sys.exit(1)
    else:
        logger.info("Environment check passed. Required variables are set.")

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

def process_command(args):
    """Run the PDF processing command"""
    logger.info(f"Processing PDFs from directory: {args.pdf_dir}")
    
    try:
        # Import here to avoid circular imports
        from main import process_pdfs
        
        # Process PDFs
        start_time = time.time()
        result = process_pdfs(
            pdf_dir=args.pdf_dir,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            force=args.force
        )
        elapsed_time = time.time() - start_time
        
        # Print processing summary
        logger.info("=" * 60)
        logger.info("PDF PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total PDFs processed:    {result['total_pdfs']}")
        logger.info(f"Total text chunks:       {result['total_chunks']}")
        logger.info(f"Chunks indexed:          {result['indexed_chunks']}")
        
        if result.get('failed_chunks', 0) > 0:
            logger.warning(f"Chunks failed (rate limit): {result['failed_chunks']}")
            logger.warning("Some chunks could not be embedded due to API rate limits.")
            logger.warning("The successfully embedded chunks have been stored in the database.")
        
        if result.get('errors', 0) > 0:
            logger.warning(f"Documents with errors:   {result['errors']}")

        success_pct = (result['indexed_chunks'] / result['total_chunks'] * 100) if result['total_chunks'] > 0 else 0
        logger.info(f"Success rate:            {success_pct:.1f}%")
        logger.info(f"Processing time:         {elapsed_time:.2f} seconds")
        logger.info("=" * 60)
        
        # Show next steps
        logger.info("\nNext steps:")
        logger.info("  - Run a search query with: python -m vector_search_mistral.run search \"your query\"")
        logger.info("  - Try enhanced RAG search with: python -m vector_search_mistral.run search \"your query\" --rag")
        
        if result.get('failed_chunks', 0) > 0:
            logger.info("\nSuggestion for rate limits:")
            logger.info("  - Wait a few minutes before processing more PDFs")
            logger.info("  - Consider processing smaller batches of PDFs")
            logger.info("  - Check your Mistral AI account rate limits")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        if "--debug" in sys.argv:
            traceback.print_exc()
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
    if not load_root_env_vars():
        return 1
    
    check_env_vars(args)
    
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
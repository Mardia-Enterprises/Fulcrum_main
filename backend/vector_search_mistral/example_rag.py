#!/usr/bin/env python3
"""
Example script demonstrating RAG (Retrieval-Augmented Generation) with OpenAI.
This script shows how to combine vector search with OpenAI to enhance search results.
"""

import os
import sys
import json
from pathlib import Path

# Get the absolute path to the project root
project_root = str(Path(__file__).parent.parent.parent.absolute())

# Clean up sys.path to avoid duplicate entries
if project_root in sys.path:
    sys.path.remove(project_root)

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv package not found. Environment variables must be set manually.")

# Import modules
try:
    from backend.vector_search_mistral.main import search_pdfs
    from backend.vector_search_mistral.openai_processor import process_rag_results, OpenAIProcessor
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've activated the virtual environment:")
    print(f"    source {project_root}/backend/.venv/bin/activate")
    print("And installed the required packages:")
    print(f"    pip install -r {project_root}/backend/vector_search_mistral/requirements.txt")
    sys.exit(1)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ["MISTRAL_API_KEY", "PINECONE_API_KEY", "PINECONE_REGION"]
    optional_vars = ["OPENAI_API_KEY"]
    
    missing_required = [var for var in required_vars if not os.environ.get(var)]
    missing_optional = [var for var in optional_vars if not os.environ.get(var)]
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"  - {var}")
        print("\nPlease set these variables in a .env file or in your environment.")
        return False
    
    if missing_optional:
        print("⚠️ Warning: Some optional environment variables are not set:")
        for var in missing_optional:
            print(f"  - {var}")
        print("The RAG features will not work without an OpenAI API key.")
        return True
    
    print("✅ All required environment variables are set!")
    return True

def main():
    """Demonstrate RAG capabilities with a sample query."""
    if not check_environment():
        return
    
    # Check if OpenAI API key is available
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("\n❌ OpenAI API key not found. Skipping RAG demonstration.")
        print("Please set OPENAI_API_KEY in your .env file to use RAG features.")
        return
    
    print("\n=== PDF Search with RAG Demonstration ===\n")
    
    # Define example queries
    queries = [
        "What is vector search?",
        "How does RAG work?",
        "What are the limitations of PDF processing?"
    ]
    
    # Define RAG modes to demonstrate
    rag_modes = ["summarize", "explain", "analyze", "detail"]
    
    # Choose one query and one mode for the example
    query = queries[0]  # "What is vector search?"
    mode = "explain"
    
    print(f"Query: '{query}'")
    print(f"RAG Mode: {mode}")
    print("\nSearching documents...")
    
    # Search for documents
    results = search_pdfs(query=query, top_k=5, alpha=0.5)
    
    if not results:
        print("\nℹ️ No search results found. Try processing some PDF files first:")
        print(f"  ./backend/vector_search_mistral/pdf-search process --pdf-dir pdf_data/example-pdfs")
        return
    
    print(f"\nFound {len(results)} search results")
    
    # Process with OpenAI RAG
    print("\nEnhancing results with OpenAI...")
    
    processor = OpenAIProcessor()
    rag_result = processor.summarize_search_results(
        query=query,
        search_results=results,
        mode=mode
    )
    
    # Display the results
    print("\n=== Enhanced Results ===\n")
    
    if "error" in rag_result:
        print(f"Error: {rag_result['error']}")
    else:
        print(rag_result["processed_result"])
    
    # Show how to try different modes
    print("\n=== Try Different Modes ===")
    print("You can process the same search results with different modes:")
    
    for m in rag_modes:
        if m != mode:
            print(f"\n$ ./backend/vector_search_mistral/pdf-search search \"{query}\" --rag --rag-mode {m}")
    
    print("\n=== Example Complete ===")

if __name__ == "__main__":
    main() 
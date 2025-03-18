#!/usr/bin/env python3
"""
Example script showing how to use the PDF search engine API.
"""

import os
import sys
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
    from backend.vector_search_mistral.main import process_and_index_pdfs, search_pdfs
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
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in a .env file or in your environment.")
        return False
    
    print("✅ All required environment variables are set!")
    return True

def main():
    # Verify we're running in the correct virtual environment
    venv_path = os.path.join(project_root, 'backend', '.venv')
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment.")
        print(f"It is recommended to activate the virtual environment first:")
        print(f"    source {venv_path}/bin/activate")
    
    if not check_environment():
        return
    
    # Example 1: Process a directory of PDF files
    print("\n# Example 1: Process PDF files")
    print("----------------------------")
    
    pdf_dir = "pdf_data/raw-files"
    
    # Create directory if needed, but don't download a sample PDF
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir, exist_ok=True)
        print(f"Created directory: {pdf_dir}")
    
    # Process PDFs if there are any in the directory
    pdf_files = list(Path(pdf_dir).glob("**/*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}. Please add PDF files to continue.")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}.")
    print("Processing PDF files...")
    
    stats = process_and_index_pdfs(
        pdf_dir=pdf_dir,
        chunk_size=512,
        chunk_overlap=128,
        force_reprocess=False
    )
    
    print("\nProcessing complete!")
    print(f"Total PDFs processed: {stats['total_pdfs']}")
    print(f"Total chunks created: {stats['total_chunks']}")
    print(f"Total embeddings generated: {stats['total_embeddings']}")
    print(f"Total vectors indexed: {stats['total_indexed']}")
    print(f"Errors: {stats['errors']}")
    
    # Example 2: Search for documents
    print("\n# Example 2: Search PDF content")
    print("-----------------------------")
    
    # Define some example queries
    example_queries = [
        "What is attention in machine learning?",
        "Explain self-attention mechanism",
        "What are the advantages of transformer models?"
    ]
    
    for query in example_queries:
        print(f"\nQuery: '{query}'")
        results = search_pdfs(query=query, top_k=3, alpha=0.5)
        
        if not results:
            print("No results found.")
            continue
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Document: {result['filename']}")
            print(f"Score: {result['score']:.4f}")
            print("Text snippets:")
            
            # Show up to 2 text matches per result
            for j, match in enumerate(result['text_matches'][:2]):
                print(f"  Snippet {j+1}: {match['text'][:150]}...")
            
            if len(result['text_matches']) > 2:
                print(f"  ... and {len(result['text_matches']) - 2} more snippets")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 
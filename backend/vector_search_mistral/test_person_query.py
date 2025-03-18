#!/usr/bin/env python3
"""
Test script to demonstrate the person query functionality.
This script directly uses the OpenAI processor to test person queries.
"""

import os
import sys
from pathlib import Path
import json

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

# Sample search results for testing
SAMPLE_RESULTS = [
    {
        "id": "doc1_0",
        "score": 0.8,
        "text": "The project team includes Manish Mardia as the lead engineer responsible for system design. He previously worked on the W912BV20R0005 Tulsa IDC project.",
        "metadata": {"filename": "W912BV20R0005 Tulsa IDC SMALL BUSINESS_FINAL DRAFT.pdf"}
    },
    {
        "id": "doc2_1",
        "score": 0.7,
        "text": "Manish Mardia contributed to the W9126G20R0005 response as a senior engineer, providing technical oversight and quality control.",
        "metadata": {"filename": "W9126G20R0005 RESPONSE MHZ JV DLA SF330 Part I and Part II.pdf"}
    },
    {
        "id": "doc3_2",
        "score": 0.6,
        "text": "The project was completed under the guidance of Manish Mardia, who served as the project manager for W912P824R0023.",
        "metadata": {"filename": "W912P824R0023_EI-MSMM_Engineering_LLC-16Apr2024-Red.pdf"}
    },
    {
        "id": "doc4_3",
        "score": 0.5,
        "text": "Technical specifications were reviewed by Manish Mardia, who has extensive experience in civil works from his involvement in the W912EQ24R0001 project.",
        "metadata": {"filename": "W912EQ24R0001_MVM_DB_CivilWorks-Donald_Bond_Construction,Inc.-2July2024.pdf"}
    },
    {
        "id": "doc5_4",
        "score": 0.4,
        "text": "Manish Mardia was a key contributor to the W9126G20R0099 small business response, where he provided engineering expertise.",
        "metadata": {"filename": "W9126G20R0099 MHZ JV Response to A-E CPS for SWD SWF Military and Civil Works MATOC [SMALL BUSINESS].pdf"}
    }
]

def test_person_query():
    """Test the person query functionality."""
    print("Testing person query functionality...\n")
    
    try:
        from backend.vector_search_mistral.openai_processor import OpenAIProcessor
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you've activated the virtual environment:")
        print(f"    source {project_root}/backend/.venv/bin/activate")
        return
    
    # Check if OpenAI API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment.")
        print("Please set this variable in your .env file.")
        return
    
    print("✅ OPENAI_API_KEY found in environment.")
    
    # Create processor
    processor = OpenAIProcessor()
    
    # Test person name extraction
    print("\n--- Testing Person Name Extraction ---")
    test_queries = [
        "Give me all projects that Manish Mardia has worked on",
        "What has John Smith been working on?",
        "Projects by Jane Doe",
        "Show me work done by Robert Johnson"
    ]
    
    for query in test_queries:
        is_person = processor.is_person_query(query)
        name = processor.extract_person_name(query) if is_person else None
        print(f"Query: '{query}'")
        print(f"  Is person query: {is_person}")
        print(f"  Extracted name: {name}")
    
    # Test person summary generation
    print("\n--- Testing Person Summary Generation ---")
    
    # Create a query about Manish Mardia
    query = "Give me all projects that Manish Mardia has worked on"
    
    print(f"Query: '{query}'")
    print("Processing with sample data...")
    
    # Process the query
    result = processor.summarize_search_results(
        query=query,
        search_results=SAMPLE_RESULTS,
        mode="person"
    )
    
    # Display the result
    print("\n--- Result ---\n")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Person Name: {result.get('person_name', 'Not detected')}")
        print("\nProcessed Result:")
        print(result["processed_result"])
    
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    test_person_query() 
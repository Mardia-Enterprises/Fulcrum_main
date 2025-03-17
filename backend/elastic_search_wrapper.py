#!/usr/bin/env python3
import sys
import json
import traceback

try:
    # Import the search_documents function from the query_engine_elasticsearch module
    from query_engine_elasticsearch import search_documents
    
    # Get the query from command line arguments
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)
    
    query = sys.argv[1]
    
    # Call the search_documents function
    results = search_documents(query)
    
    # Format the results
    formatted_results = []
    
    if results:
        for res in results:
            formatted_result = {
                "file_name": res.get("file_name", "Unknown"),
                "chunk_id": res.get("chunk_id", "Unknown"),
                "highlight": res.get("highlight", "No highlight available"),
                "type": "elastic_search_result"
            }
            formatted_results.append(formatted_result)
    
    # Only output the JSON, no additional text
    # Make sure there's nothing else printed to stdout
    print(json.dumps(formatted_results))

except Exception as e:
    error_message = {
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    print(json.dumps(error_message))
    sys.exit(1) 
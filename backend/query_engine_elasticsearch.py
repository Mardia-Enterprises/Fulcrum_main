"""
Mock implementation of Elasticsearch query engine.
This is a placeholder until the actual implementation is available.
"""

def search_documents(query):
    """
    Mock function to search documents using Elasticsearch.
    In a real implementation, this would connect to Elasticsearch and perform a search.
    
    Args:
        query (str): The search query
        
    Returns:
        list: A list of search results
    """
    # Debug print statement removed to avoid breaking JSON parsing
    # print(f"Searching for: {query}")
    
    # Convert query to lowercase for easier matching
    query_lower = query.lower()
    
    # Return different mock results based on the query
    if "cow bayou" in query_lower or "drainage pump" in query_lower or "pump station" in query_lower:
        return [
            {
                "file_name": "drainage_pump_specs.pdf",
                "chunk_id": "1",
                "highlight": "The Cow Bayou Drainage Pump Station Complex design includes three 48-inch diameter pumps with a combined capacity of 900 CFS."
            },
            {
                "file_name": "project_timeline.pdf",
                "chunk_id": "3",
                "highlight": "Phase 1 of the Cow Bayou project is scheduled for completion in Q3 2023, with final commissioning in Q4."
            },
            {
                "file_name": "environmental_impact.pdf",
                "chunk_id": "7",
                "highlight": "The Cow Bayou project has received environmental clearance after addressing concerns about wildlife habitats in the surrounding wetlands."
            }
        ]
    elif "texas" in query_lower or "transportation" in query_lower or "department" in query_lower:
        return [
            {
                "file_name": "txdot_projects.pdf",
                "chunk_id": "2",
                "highlight": "The Texas Department of Transportation (TxDOT) has approved funding for 3 new infrastructure projects in the coastal region."
            },
            {
                "file_name": "highway_expansion.pdf",
                "chunk_id": "5",
                "highlight": "TxDOT's Highway 87 expansion will improve evacuation routes during hurricane season and provide better access to coastal communities."
            },
            {
                "file_name": "bridge_inspection.pdf",
                "chunk_id": "9",
                "highlight": "Annual bridge inspections by TxDOT revealed that 85% of the county's bridges are in good condition, with 15% requiring maintenance."
            }
        ]
    elif "abc" in query_lower:
        return [
            {
                "file_name": "construction_methods.pdf",
                "chunk_id": "4",
                "highlight": "The Accelerated Bridge Construction (ABC) technique will be used to minimize traffic disruption during the replacement of the Main Street Bridge."
            },
            {
                "file_name": "project_glossary.pdf",
                "chunk_id": "12",
                "highlight": "ABC (Accelerated Bridge Construction) is a modern construction method that reduces on-site construction time while improving safety and quality."
            }
        ]
    else:
        # Generic results for other queries
        return [
            {
                "file_name": "general_information.pdf",
                "chunk_id": "1",
                "highlight": f"Your search for '{query}' did not match specific documents. Here is some general information about engineering projects."
            },
            {
                "file_name": "search_tips.pdf",
                "chunk_id": "2",
                "highlight": "Try using more specific terms related to projects, locations, or engineering specifications to get better results."
            }
        ] 
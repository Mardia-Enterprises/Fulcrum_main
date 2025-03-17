import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Print environment variables (without revealing API keys)
print("Environment variables loaded:")
print(f"PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME')}")
print(f"PINECONE_REGION: {os.getenv('PINECONE_REGION')}")
print(f"PINECONE_API_KEY exists: {'Yes' if os.getenv('PINECONE_API_KEY') else 'No'}")
print(f"OPENAI_API_KEY exists: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"MISTRAL_API_KEY exists: {'Yes' if os.getenv('MISTRAL_API_KEY') else 'No'}")

try:
    # Initialize Pinecone
    print("\nInitializing Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    # List indexes
    print("\nListing Pinecone indexes...")
    indexes = pc.list_indexes()
    print(f"Available indexes: {indexes.names() if hasattr(indexes, 'names') else indexes}")
    
    # Define the index name
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    # Check if index exists, otherwise create one
    if index_name not in (indexes.names() if hasattr(indexes, 'names') else []):
        print(f"\nCreating index '{index_name}'...")
        pc.create_index(
            name=index_name, 
            dimension=1536,  # Updated to match text-embedding-3-small's actual dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",  
                region=os.getenv("PINECONE_REGION")
            )
        )
        print(f"Index '{index_name}' created successfully!")
    else:
        print(f"\nIndex '{index_name}' already exists.")
    
    # Connect to the index
    print(f"\nConnecting to index '{index_name}'...")
    index = pc.Index(index_name)
    
    # Test vector insertion
    print("\nTesting vector insertion...")
    test_vector = [0.1] * 1536  # Create a test vector with 1536 dimensions
    
    index.upsert(vectors=[{
        "id": "test_vector",
        "values": test_vector,
        "metadata": {
            "test": "This is a test vector"
        }
    }])
    
    print("Test vector inserted successfully!")
    
    # Test vector query
    print("\nTesting vector query...")
    results = index.query(vector=test_vector, top_k=1, include_metadata=True)
    print(f"Query results: {json.dumps(results.to_dict(), indent=2)}")
    
    # Clean up test vector
    print("\nCleaning up test vector...")
    index.delete(ids=["test_vector"])
    print("Test vector deleted successfully!")
    
    print("\nPinecone test completed successfully!")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc() 
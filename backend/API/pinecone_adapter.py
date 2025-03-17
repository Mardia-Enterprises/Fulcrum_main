import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Pinecone with the current API
def initialize_pinecone():
    """Initialize Pinecone with the current API"""
    api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=api_key)
    
    # Define the index name
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    # Check if index exists, otherwise create one
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # Match the dimension in datauploader.py
            metric="cosine"
        )
    
    # Connect to the index
    return pc.Index(index_name)

# Get the pinecone index
index = initialize_pinecone()

def query_index(vector, top_k=10, include_metadata=True):
    """Query the pinecone index"""
    return index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=include_metadata
    )

def fetch_vectors(ids):
    """Fetch vectors by IDs"""
    return index.fetch(ids=ids)

def delete_vectors(ids):
    """Delete vectors by IDs"""
    return index.delete(ids=ids) 
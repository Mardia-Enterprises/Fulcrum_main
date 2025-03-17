from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import os

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("contract-search")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def search_documents(query_text):
    """Search for documents in Pinecone based on the query text."""
    query_embedding = model.encode([query_text]).tolist()

    # Query Pinecone
    search_results = index.query(vector=query_embedding, top_k=5, include_metadata=True)

    results = []
    for match in search_results["matches"]:
        results.append({
            "file_name": match["metadata"]["file_name"],
            "chunk_id": match["metadata"]["chunk_id"],
            "text": match["metadata"]["text"]
        })

    return results

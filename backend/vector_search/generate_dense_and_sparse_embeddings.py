from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import pinecone
import json
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Initialize Pinecone instance
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Define the index name
index_name = "contract-search"

# Check if index exists, otherwise create one
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name, 
        dimension=384,  # Adjust dimension based on model
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  
            region=os.getenv("PINECONE_REGION")  # Ensure region is correctly set
        )
    )

# Connect to the index
index = pc.Index(index_name)


# Load transformer model (Dense)
dense_model = SentenceTransformer("all-MiniLM-L6-v2")

RAW_FOLDER = "raw-files"
PROCESSED_FOLDER = "processed-files-vector"


def get_bm25_embeddings(texts):
    """Generate BM25 sparse embeddings for keyword-based retrieval."""
    tokenized_texts = [text.split() for text in texts]
    bm25 = BM25Okapi(tokenized_texts)
    return [bm25.get_scores(query.split()) for query in texts]

def store_embeddings():
    """Generate and store embeddings in Pinecone."""
    for txt_file in os.listdir(PROCESSED_FOLDER):
        if txt_file.endswith(".txt"):
            txt_path = os.path.join(PROCESSED_FOLDER, txt_file)
            
            with open(txt_path, "r", encoding="utf-8") as f:
                chunks = f.readlines()

            # Generate Dense & Sparse embeddings
            dense_embeddings = dense_model.encode(chunks).tolist()
            sparse_embeddings = get_bm25_embeddings(chunks)

            # Store in Pinecone
            for i, (dense_emb, sparse_emb) in enumerate(zip(dense_embeddings, sparse_embeddings)):
                index.upsert(vectors=[{
                    "id": f"{txt_file}_{i}",
                    "values": dense_emb, 
                    "metadata": {"file_name": txt_file, "chunk_id": i, "text": chunks[i]}
                }])

            print(f"✔ Stored {len(chunks)} chunks from {txt_file}")

# Run embedding storage
store_embeddings()

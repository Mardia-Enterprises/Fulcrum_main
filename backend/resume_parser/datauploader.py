import os
import json
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 🔹 Initialize OpenAI for embeddings
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Pinecone instance
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Define the index name
index_name = os.getenv("PINECONE_INDEX_NAME")

# Check if index exists, otherwise create one
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name, 
        dimension=1536,  # Updated to match text-embedding-3-small's actual dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",  
            region=os.getenv("PINECONE_REGION")  # Ensure region is correctly set
        )
    )

# Connect to the index
index = pc.Index(index_name)


def generate_embedding(text):
    """Generates an embedding using OpenAI's 1536-dimension model."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # This model outputs 1536-dimensional vectors
    )
    return response.data[0].embedding


def upsert_resume_in_pinecone(employee_name, file_id, resume_data):
    """Stores an employee resume as a vector in Pinecone."""
    
    # Convert structured resume data to a JSON string
    resume_text = json.dumps(resume_data, indent=4)

    # Generate an embedding for the resume
    embedding = generate_embedding(resume_text)

    # Upsert into Pinecone with metadata (convert resume_data to a string)
    index.upsert(vectors=[{
        "id": f"{employee_name}",
        "values": embedding,
        "metadata": {
            "employee_name": employee_name,
            "file_id": [file_id],
            "resume_data": resume_text  # ✅ Convert dict to JSON string
        }
    }])

    print(f"✅ Stored resume `{file_id}` for `{employee_name}` in Pinecone")

def query_employees(query_text):
    query_embedding = generate_embedding(query_text)
    results = index.query(vector=query_embedding, top_k=10, include_metadata=True)
    return results

# 🔹 Example Resume Data for Testing

# Example query
if __name__ == "__main__":
    # Query for employees with project management experience
    search_query = "find me my best hydraulic engineers"
    results = query_employees(search_query)
    
    print("\nSearch Results:")
    print("--------------")
    for match in results.matches:
        employee_data = json.loads(match.metadata["resume_data"])
        print(f"\nEmployee: {employee_data['Name']}")
        print(f"Score: {match.score:.3f}")
        print(f"Role: {employee_data.get('Role in Contract', 'Not provided in the given information.')}")
        print("Relevant Projects:")
        for project in employee_data.get('Relevant Projects', []):
            if isinstance(project, dict):
                print(f"- {project.get('Title', 'Untitled')}")



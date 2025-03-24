import os
import json
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# 🔹 Initialize OpenAI for embeddings
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Initialize Supabase client
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
supabase = create_client(supabase_url, supabase_key)

# Define the collection name (table name in Supabase)
collection_name = "section_f_projects"

def generate_embedding(text):
    """Generates an embedding using OpenAI's 1536-dimension model."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # This model outputs 1536-dimensional vectors
    )
    return response.data[0].embedding

def upsert_resume_in_supabase(project_key, file_id, resume_data):
    """Stores an employee resume as a vector in Supabase."""
    
    # Convert structured resume data to a JSON string
    resume_text = json.dumps(resume_data, indent=4)

    # Generate an embedding for the resume
    embedding = generate_embedding(resume_text)
    
    # Create a unique ID if none provided
    if not file_id:
        file_id = str(uuid.uuid4())
    
    # Convert employee name to a valid id by replacing spaces with underscores
    project_id = project_key.lower().replace(' ', '_')
    
    # Prepare data for Supabase
    vector_data = {
        "id": project_id,
        "project_key": project_key,
        "file_id": file_id,
        "resume_data": resume_data,  # Store as JSON in Supabase
        "embedding": embedding
    }
    
    # Upsert into Supabase vector collection
    result = supabase.table(collection_name).upsert(vector_data).execute()
    
    if hasattr(result, 'error') and result.error:
        print(f"❌ Error storing resume for `{project_key}` in Supabase: {result.error}")
    else:
        print(f"✅ Successfully stored resume for `{project_key}` in Supabase")
    
    return project_id

def query_projects(query_text, top_k=10):
    """Query project data using vector similarity search."""
    # Generate embedding for the query
    query_embedding = generate_embedding(query_text)
    
    # Perform vector similarity search in Supabase
    result = supabase.rpc(
        'match_projects',  # Function name must match your Supabase RPC function
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.5,  # Adjust as needed
            'match_count': top_k
        }
    ).execute()
    
    if hasattr(result, 'error') and result.error:
        print(f"❌ Error querying projects: {result.error}")
        return []
    
    return result.data

# Example query
if __name__ == "__main__":
    # Query for projects with project management experience
    search_query = "find me my best hydraulic engineers"
    results = query_projects(search_query)
    
    print("\nSearch Results:")
    print("--------------")
    for match in results:
        project_data = match.get("resume_data", {})
        print(f"\nProject: {project_data.get('name', 'Unknown')}")
        print(f"Score: {match.get('similarity', 0):.3f}")
        print(f"Role: {project_data.get('role', ['Not provided'])}")
        print("Relevant Projects:")
        for project in project_data.get('relevant_projects', []):
            if isinstance(project, dict):
                print(f"- {project.get('title_and_location', 'Untitled')}")



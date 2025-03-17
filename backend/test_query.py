import os
import json
from Resume_Parser.datauploader import query_employees
from dotenv import load_dotenv

load_dotenv()

def test_query(search_query):
    print(f"Searching for: '{search_query}'")
    results = query_employees(search_query)
    
    print("\nSearch Results:")
    print("--------------")
    
    if not results.matches:
        print("No matches found.")
        return
    
    for match in results.matches:
        employee_data = json.loads(match.metadata["resume_data"])
        print(f"\nEmployee: {employee_data['Name']}")
        print(f"Score: {match.score:.3f}")
        print(f"Role: {employee_data.get('Role in Contract', 'Not provided')}")
        
        # Print education if available
        education = employee_data.get('Education', 'Not provided')
        if isinstance(education, list) and education:
            print("Education:")
            for edu in education:
                if isinstance(edu, dict):
                    degree = edu.get('Degree', 'Not specified')
                    specialization = edu.get('Specialization', 'Not specified')
                    print(f"- {degree} in {specialization}")
                else:
                    print(f"- {edu}")
        elif isinstance(education, str):
            print(f"Education: {education}")
        
        # Print relevant projects if available
        projects = employee_data.get('Relevant Projects', [])
        if projects:
            print("Relevant Projects:")
            for project in projects:
                if isinstance(project, dict):
                    title = project.get('Title', 'Untitled')
                    role = project.get('Role', 'Not specified')
                    print(f"- {title} (Role: {role})")
                else:
                    print(f"- {project}")

if __name__ == "__main__":
    # Test different queries
    queries = [
        "hydraulic engineers with experience in flood control",
        "project managers with LEED certification",
        "civil engineers with bridge design experience",
        "engineers with experience in water resources"
    ]
    
    for query in queries:
        test_query(query)
        print("\n" + "="*50 + "\n") 
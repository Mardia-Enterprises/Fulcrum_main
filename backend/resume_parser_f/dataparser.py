import os
import json
import sys
from mistralai import Mistral
from dotenv import load_dotenv
import uuid
from supabase import create_client
from openai import OpenAI

# Import the Supabase uploader function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resume_parser.datauploader import upsert_resume_in_supabase

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

# Initialize OpenAI for embeddings
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_PROJECT_URL")
supabase_key = os.getenv("SUPABASE_PRIVATE_API_KEY")
supabase = create_client(supabase_url, supabase_key)

def generate_embedding(text):
    """Generates an embedding using OpenAI's 1536-dimension model."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # This model outputs 1536-dimensional vectors
    )
    return response.data[0].embedding

def upsert_project_in_supabase(project_title, file_id, project_data):
    """Stores a project as a vector in Supabase."""
    
    # Ensure project_title is a string
    if isinstance(project_title, list):
        project_title = ", ".join(project_title)
    
    # Convert structured project data to a JSON string
    project_text = json.dumps(project_data, indent=4)

    # Generate an embedding for the project
    embedding = generate_embedding(project_text)
    
    # Create a unique ID if none provided
    if not file_id:
        file_id = str(uuid.uuid4())
    
    # Convert project title to a valid id by replacing spaces with underscores
    project_id = project_title.lower().replace(' ', '_').replace(',', '')
    
    # Prepare data for Supabase - matching the schema from section_f_projects_supabase.sql
    vector_data = {
        "id": project_id,
        "project_key": project_title,  # Changed from project_title to project_key
        "file_id": file_id,
        "project_data": project_data,
        "embedding": embedding
    }
    
    # Upsert into Supabase vector collection
    result = supabase.table("section_f_projects").upsert(vector_data).execute()
    
    if hasattr(result, 'error') and result.error:
        print(f"❌ Error storing project for `{project_title}` in Supabase: {result.error}")
    else:
        print(f"✅ Successfully stored project for `{project_title}` in Supabase")
    
    return project_id

def upload_pdf_to_mistral(pdf_path):
    """Uploads a PDF to Mistral AI for OCR processing."""
    print(f"Uploading {pdf_path} to Mistral AI...")
    
    with open(pdf_path, "rb") as file:
        uploaded_pdf = client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": file,
            },
            purpose="ocr"
        )
    
    # Get a signed URL for the uploaded file
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    
    return signed_url.url

def extract_structured_data_with_mistral(pdf_url):
    """Uses Mistral AI LLM to structure extracted text from Section F resumes."""
    print("Processing structured data extraction with Mistral AI...")

    system_prompt = """
        Extract the following specific information from the Section F example project description and format it as a structured JSON object with exactly the specified fields and format:

        1. title_and_location: Combine the project title and city/state into a single string (e.g., "Granger Lake Management Office Building Design, Granger, TX").

        2. year_completed: A dictionary with two integer fields:
        - professional_services: Year the design/professional services were completed (e.g., 2019)
        - construction: Year the construction was completed (e.g., 2021)
        If construction year is missing, set it to null.

        3. project_owner: The name of the owner organization (e.g., "USACE Fort Worth District").

        4. point_of_contact_name: Full name and title of the POC, including email address if listed 
        (e.g., "Sharon Leheny, Project Manager – Sharon.v.leheny@usace.army.mil").

        5. point_of_contact_telephone_number: Just the phone number (e.g., "817-886-1563").

        6. brief_description: A rich and complete project narrative. Include:
        - project goals and design intent
        - size, area (SF), and building features
        - sustainability and HVAC/mechanical system info
        - any relevant timelines or unique constraints
        - sewer or water system details
        The description should be a single multiline string. Maintain paragraph structure.

        7. firms_from_section_c_involved_with_this_project: A list of firms that worked on this project with exactly these fields per firm:
        - firm_name: Name of the firm (e.g., "MSMM Engineering")
        - firm_location: City and state of the firm (e.g., "New Orleans, LA")
        - role: Description of the firm's role (e.g., "Prime: Architecture, Civil, Structural, and MEP")

        Rules:
        - Do not skip any fields. If something is not available, write "Not provided" or null as appropriate.
        - Ensure proper punctuation and formatting in all strings.
        - Extract the information as-is from the text, without paraphrasing unless necessary to normalize format.
        - Return the result as a valid JSON object.
        """


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [{"type": "document_url", "document_url": pdf_url}]}
    ]

    response = client.chat.complete(
        model="mistral-small",  # Using a more capable model for better extraction
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,  # Lower temperature for more deterministic outputs
        max_tokens=4000  # Increased token limit to ensure complete extraction
    )

    json_text = response.choices[0].message.content  # This is a string
    try:
        structured_data = json.loads(json_text)  # Convert string to dictionary

        # Ensure all expected fields are present with their correct types
        if 'title_and_location' not in structured_data:
            structured_data['title_and_location'] = "Unknown"

        if 'year_completed' not in structured_data or not isinstance(structured_data['year_completed'], dict):
            structured_data['year_completed'] = {
                "professional_services": None,
                "construction": None
            }
        else:
            if 'professional_services' not in structured_data['year_completed']:
                structured_data['year_completed']['professional_services'] = None
            if 'construction' not in structured_data['year_completed']:
                structured_data['year_completed']['construction'] = None

        if 'project_owner' not in structured_data:
            structured_data['project_owner'] = "Not provided"

        if 'point_of_contact_name' not in structured_data:
            structured_data['point_of_contact_name'] = "Not provided"

        if 'point_of_contact_telephone_number' not in structured_data:
            structured_data['point_of_contact_telephone_number'] = "Not provided"

        if 'brief_description' not in structured_data:
            structured_data['brief_description'] = "Not provided"

        if 'firms_from_section_c_involved_with_this_project' not in structured_data or not isinstance(structured_data['firms_from_section_c_involved_with_this_project'], list):
            structured_data['firms_from_section_c_involved_with_this_project'] = []
        else:
            for i, firm in enumerate(structured_data['firms_from_section_c_involved_with_this_project']):
                if not isinstance(firm, dict):
                    structured_data['firms_from_section_c_involved_with_this_project'][i] = {
                        "firm_name": "Unknown",
                        "firm_location": "Unknown",
                        "role": "Not provided"
                    }
                    continue

                if 'firm_name' not in firm:
                    firm['firm_name'] = "Unknown"
                if 'firm_location' not in firm:
                    firm['firm_location'] = "Unknown"
                if 'role' not in firm:
                    firm['role'] = "Not provided"

        return structured_data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {
            "title_and_location": "Unknown",
            "error": "Failed to parse response"
        }


def process_section_e_pdfs(folder_path):
    """Processes all SF 330 Section-F project descriptions in a folder."""
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return

    project_data = {}

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Starting processing for: {pdf_path}")

        try:
            # ✅ Step 1: Upload PDF and get a signed URL
            pdf_url = upload_pdf_to_mistral(pdf_path)

            # ✅ Step 2: Extract structured JSON data using Section-F prompt
            structured_data = extract_structured_data_with_mistral(pdf_url)

            # ✅ Step 3: Validate and normalize
            if not isinstance(structured_data, dict):
                print(f"Invalid data structure in {pdf_file}: expected dictionary")
                continue

            # Fill in missing or malformed fields with defaults
            structured_data.setdefault('title_and_location', "Unknown")
            structured_data.setdefault('year_completed', {
                "professional_services": None,
                "construction": None
            })
            structured_data.setdefault('project_owner', "Not provided")
            structured_data.setdefault('point_of_contact_name', "Not provided")
            structured_data.setdefault('point_of_contact_telephone_number', "Not provided")
            structured_data.setdefault('brief_description', "Not provided")

            if 'firms_from_section_c_involved_with_this_project' not in structured_data or not isinstance(structured_data['firms_from_section_c_involved_with_this_project'], list):
                structured_data['firms_from_section_c_involved_with_this_project'] = []
            else:
                for i, firm in enumerate(structured_data['firms_from_section_c_involved_with_this_project']):
                    if not isinstance(firm, dict):
                        structured_data['firms_from_section_c_involved_with_this_project'][i] = {
                            "firm_name": "Unknown",
                            "firm_location": "Unknown",
                            "role": "Not provided"
                        }
                    else:
                        firm.setdefault("firm_name", "Unknown")
                        firm.setdefault("firm_location", "Unknown")
                        firm.setdefault("role", "Not provided")

            # Use title_and_location as unique key
            project_key = structured_data['title_and_location']

            # Save individual project output
            output_path = f"{project_key.replace(',', '').replace(' ', '_')}_project_data.json"
            with open(output_path, "w") as f:
                json.dump(structured_data, f, indent=2)
            print(f"Saved data to {output_path}")

            # Merge if already exists
            if project_key in project_data:
                existing = project_data[project_key]

                # Prefer earliest professional_services year
                ps_year = structured_data['year_completed'].get('professional_services')
                if ps_year and (existing['year_completed'].get('professional_services') is None or ps_year < existing['year_completed']['professional_services']):
                    existing['year_completed']['professional_services'] = ps_year

                # Prefer latest construction year
                cons_year = structured_data['year_completed'].get('construction')
                if cons_year and (existing['year_completed'].get('construction') is None or cons_year > existing['year_completed']['construction']):
                    existing['year_completed']['construction'] = cons_year

                # Merge firms without duplication
                new_firms = structured_data['firms_from_section_c_involved_with_this_project']
                existing_firms = existing.get('firms_from_section_c_involved_with_this_project', [])
                all_firms = existing_firms + new_firms
                # Deduplicate by firm_name + role
                seen = set()
                deduped = []
                for firm in all_firms:
                    key = (firm['firm_name'], firm['role'])
                    if key not in seen:
                        seen.add(key)
                        deduped.append(firm)
                existing['firms_from_section_c_involved_with_this_project'] = deduped

                project_data[project_key] = existing
            else:
                project_data[project_key] = structured_data

            # Optionally upsert to Supabase or another system
            upsert_project_in_supabase(project_key, "", structured_data)

        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    # Save merged data for all projects
    for project_key, structured_data in project_data.items():
        try:
            output_path = f"{project_key.replace(',', '').replace(' ', '_')}_merged_project_data.json"
            with open(output_path, "w") as f:
                json.dump(structured_data, f, indent=2)
            print(f"Saved merged data for {project_key} to {output_path}")

            # Optionally upsert to Supabase or another system
            upsert_project_in_supabase(project_key, "", structured_data)
        except Exception as e:
            print(f"Error saving merged data for {project_key}: {e}")


# Example usage
if __name__ == "__main__":
    # Try multiple possible locations for the PDF files
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Section F Resumes"),
        "pdf_data/Section F Resumes",
        os.path.join(os.getcwd(), "Section F Resumes"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Section F Resumes")
    ]
    
    folder_path = None
    for path in possible_paths:
        print(f"Checking for PDF files in: {path}")
        if os.path.exists(path):
            folder_path = path
            print(f"Found directory: {folder_path}")
            break
    
    if folder_path is None:
        print("Could not find the 'Section F Resumes' directory. Creating it...")
        # Create the directory in the current working directory
        folder_path = os.path.join(os.getcwd(), "Section E Resumes")
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created directory: {folder_path}")
        print("Please place your PDF files in this directory and run the script again.")
    else:
        # Check if directory has PDF files
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        if not pdf_files:
            print(f"No PDF files found in {folder_path}. Please add PDF files and run again.")
        else:
            print(f"Found {len(pdf_files)} PDF files. Starting processing...")
            process_section_e_pdfs(folder_path)

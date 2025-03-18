import os
import json
import sys
from mistralai import Mistral
from dotenv import load_dotenv

# Import the Supabase uploader function
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resume_parser.datauploader import upsert_resume_in_supabase

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

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
    """Uses Mistral AI LLM to structure extracted text from SF 330 Section E."""
    print("Processing structured data extraction with Mistral AI...")

    system_prompt = """
    Extract the following specific information from the SF 330 Section E resume and format it exactly as specified below:

    1. name: Full name of the person (e.g., "Jim Wilson")
    2. role: List of roles in contracts (e.g., ["Civil Engineer"])
    3. years_experience: The TOTAL years of experience as an integer (not with current firm)
    4. firm_name_and_location: List containing the firm name and location (e.g., ["MSMM Engineering, LLC – New Orleans, LA"])
    5. education: List of education entries exactly like: ["BS, Civil Engineering, Michigan Technological University, 1988"]
    6. current_professional_registration: List of registrations exactly like: ["Professional Engineer/Civil (1993): TX (128376), LA (35456), MI (38800), FL (85114)"]
    7. other_professional_qualifications: List of other qualifications or detailed descriptions of expertise
    8. relevant_projects: List of project objects, each with these exact fields:
       - title_and_location: Project title and location
       - scope: Detailed project description including specific responsibilities
       - cost: Project cost (e.g., "$2.1M")
       - fee: Project fee (e.g., "$339k")
       - role: List of roles for this project (e.g., ["Engineer of Record", "Civil Engineer"])

    For years of experience, always extract the TOTAL years, not the years with current firm.
    For costs and fees, include the currency symbol and units (k, M, etc.).
    If any information is missing, use "Not provided" as the value.
    For dates, convert them to a standardized format.
    
    IMPORTANT: For education and professional registration, make sure to format them as simple strings in a list, 
    not as complex objects. For example:
    - CORRECT education format: ["BS, Civil Engineering, Michigan Technological University, 1988"]
    - CORRECT registration format: ["Professional Engineer/Civil (1993): TX (128376), LA (35456), MI (38800), FL (85114)"]

    Return the data in a structured JSON object with exactly these field names. Be as precise and detailed as possible in extracting the data.
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
        if 'name' not in structured_data:
            structured_data['name'] = "Unknown"
        
        if 'role' not in structured_data or not isinstance(structured_data['role'], list):
            structured_data['role'] = []
            
        if 'years_experience' not in structured_data:
            structured_data['years_experience'] = 0
        elif isinstance(structured_data['years_experience'], str):
            # Try to convert string to integer
            try:
                structured_data['years_experience'] = int(''.join(filter(str.isdigit, structured_data['years_experience'])))
            except:
                structured_data['years_experience'] = 0
                
        if 'firm_name_and_location' not in structured_data or not isinstance(structured_data['firm_name_and_location'], list):
            structured_data['firm_name_and_location'] = []
            
        if 'education' not in structured_data or not isinstance(structured_data['education'], list):
            structured_data['education'] = []
            
        if 'current_professional_registration' not in structured_data or not isinstance(structured_data['current_professional_registration'], list):
            structured_data['current_professional_registration'] = []
            
        if 'other_professional_qualifications' not in structured_data or not isinstance(structured_data['other_professional_qualifications'], list):
            structured_data['other_professional_qualifications'] = []
            
        if 'relevant_projects' not in structured_data or not isinstance(structured_data['relevant_projects'], list):
            structured_data['relevant_projects'] = []
        else:
            # Ensure each project has the required fields
            for i, project in enumerate(structured_data['relevant_projects']):
                if not isinstance(project, dict):
                    structured_data['relevant_projects'][i] = {
                        'title_and_location': "Unknown",
                        'scope': "Not provided",
                        'cost': "Not provided",
                        'fee': "Not provided",
                        'role': []
                    }
                    continue
                    
                if 'title_and_location' not in project:
                    project['title_and_location'] = "Unknown"
                    
                if 'scope' not in project:
                    project['scope'] = "Not provided"
                    
                if 'cost' not in project:
                    project['cost'] = "Not provided"
                    
                if 'fee' not in project:
                    project['fee'] = "Not provided"
                    
                if 'role' not in project or not isinstance(project['role'], list):
                    project['role'] = []
                
        return structured_data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {"name": "Unknown", "error": "Failed to parse response"}

def process_section_e_pdfs(folder_path):
    """Processes all SF 330 PDF resumes in a given folder."""
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return

    # Dictionary to store structured data by employee name
    employee_data = {}

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Starting processing for: {pdf_path}")

        try:
            # ✅ Step 1: Upload PDF and get a signed URL
            pdf_url = upload_pdf_to_mistral(pdf_path)
            
            # ✅ Step 2: Extract structured JSON data from text
            structured_data = extract_structured_data_with_mistral(pdf_url)

            # ✅ Step 3: Normalize data for consistency
            
            # Convert education to proper format if needed
            if 'education' in structured_data and isinstance(structured_data['education'], list):
                normalized_education = []
                for edu in structured_data['education']:
                    if isinstance(edu, dict):
                        # Convert dictionary to string format
                        edu_str = f"{edu.get('degree', 'Unknown')}, {edu.get('specialization', 'Unknown')}, {edu.get('institution', 'Unknown')}"
                        if 'year' in edu:
                            edu_str += f", {edu.get('year', '')}"
                        normalized_education.append(edu_str)
                    else:
                        normalized_education.append(edu)
                structured_data['education'] = normalized_education
            
            # Convert professional registration to proper format if needed
            if 'current_professional_registration' in structured_data and isinstance(structured_data['current_professional_registration'], list):
                normalized_registration = []
                for reg in structured_data['current_professional_registration']:
                    if isinstance(reg, dict):
                        # Convert dictionary to string format
                        reg_type = reg.get('type', 'Unknown')
                        if 'year' in reg:
                            reg_type += f" ({reg.get('year', '')})"
                        
                        state_license = []
                        if 'state' in reg and 'license_number' in reg:
                            state_license.append(f"{reg['state']} ({reg['license_number']})")
                        elif 'state' in reg:
                            state_license.append(reg['state'])
                        
                        reg_str = reg_type
                        if state_license:
                            reg_str += ": " + ", ".join(state_license)
                        
                        normalized_registration.append(reg_str)
                    else:
                        normalized_registration.append(reg)
                structured_data['current_professional_registration'] = normalized_registration

            # Get employee name
            employee_name = structured_data.get("name", "Unknown")
            
            # Save the data to a JSON file for inspection
            output_path = f"{employee_name.replace(' ', '_')}_resume_data.json"
            with open(output_path, "w") as f:
                json.dump(structured_data, f, indent=2)
            print(f"Saved data to {output_path}")
            
            # If we already have data for this employee, merge it
            if employee_name in employee_data:
                existing_data = employee_data[employee_name]
                
                # Take maximum years experience
                if 'years_experience' in structured_data and structured_data['years_experience'] > existing_data.get('years_experience', 0):
                    existing_data['years_experience'] = structured_data['years_experience']
                
                # Merge roles without duplicates
                new_roles = structured_data.get('role', [])
                existing_roles = existing_data.get('role', [])
                existing_data['role'] = list(set(existing_roles + new_roles))
                
                # Merge firm locations without duplicates
                new_locations = structured_data.get('firm_name_and_location', [])
                existing_locations = existing_data.get('firm_name_and_location', [])
                existing_data['firm_name_and_location'] = list(set(existing_locations + new_locations))
                
                # Merge education without duplicates
                new_education = structured_data.get('education', [])
                existing_education = existing_data.get('education', [])
                existing_data['education'] = list(set(existing_education + new_education))
                
                # Merge professional registrations without duplicates
                new_registrations = structured_data.get('current_professional_registration', [])
                existing_registrations = existing_data.get('current_professional_registration', [])
                existing_data['current_professional_registration'] = list(set(existing_registrations + new_registrations))
                
                # Merge professional qualifications without duplicates
                new_qualifications = structured_data.get('other_professional_qualifications', [])
                existing_qualifications = existing_data.get('other_professional_qualifications', [])
                existing_data['other_professional_qualifications'] = list(set(existing_qualifications + new_qualifications))
                
                # Add new projects
                new_projects = structured_data.get('relevant_projects', [])
                existing_projects = existing_data.get('relevant_projects', [])
                
                # Check for duplicate projects (by title) and merge if needed
                for new_project in new_projects:
                    is_duplicate = False
                    for i, existing_project in enumerate(existing_projects):
                        if new_project.get('title_and_location') == existing_project.get('title_and_location'):
                            # Found duplicate project, merge roles
                            is_duplicate = True
                            new_roles = new_project.get('role', [])
                            existing_roles = existing_project.get('role', [])
                            existing_projects[i]['role'] = list(set(existing_roles + new_roles))
                            break
                    
                    if not is_duplicate:
                        existing_projects.append(new_project)
                
                employee_data[employee_name] = existing_data
            else:
                # First time seeing this employee
                employee_data[employee_name] = structured_data
        
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    # Save merged data for all employees
    for employee_name, structured_data in employee_data.items():
        try:
            # Save to a JSON file
            output_path = f"{employee_name.replace(' ', '_')}_merged_data.json"
            with open(output_path, "w") as f:
                json.dump(structured_data, f, indent=2)
            print(f"Saved merged data for {employee_name} to {output_path}")
            
            # Upsert to Supabase
            upsert_resume_in_supabase(employee_name, "", structured_data)
        except Exception as e:
            print(f"Error saving data for {employee_name}: {e}")

# Example usage
if __name__ == "__main__":
    # Try multiple possible locations for the PDF files
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Section E Resumes"),
        "pdf_data/Section E Resumes",
        os.path.join(os.getcwd(), "Section E Resumes"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Section E Resumes")
    ]
    
    folder_path = None
    for path in possible_paths:
        print(f"Checking for PDF files in: {path}")
        if os.path.exists(path):
            folder_path = path
            print(f"Found directory: {folder_path}")
            break
    
    if folder_path is None:
        print("Could not find the 'Section E Resumes' directory. Creating it...")
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

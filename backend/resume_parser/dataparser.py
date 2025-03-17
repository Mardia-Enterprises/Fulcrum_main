import os
import json
from mistralai import Mistral
from Resume_Parser.datauploader import upsert_resume_in_pinecone
from dotenv import load_dotenv

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

    system_prompt = """Extract the following information from the SF 330 Section E resume:
    - Name
    - Role in Contract
    - Years of Experience (Total & With Current Firm)
    - Firm Name & Location
    - Education (Degree & Specialization)
    - Professional Registrations (State & License #)
    - Other Professional Qualifications
    - Relevant Projects (Title, Location, Year Completed, Description, Cost, Role)
    
    Make sure not to forget to pull full descriptions from the resume. Format the response as structured JSON. For empty values, use \"NA\" or \"Not provided in the given information.\"
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [{"type": "document_url", "document_url": pdf_url}]}
    ]

    response = client.chat.complete(
        model="mistral-tiny",
        messages=messages,
        response_format={"type": "json_object"}
    )

    json_text = response.choices[0].message.content  # This is a string
    structured_data = json.loads(json_text)  # Convert string to dictionary
    return structured_data

def process_section_e_pdfs(folder_path):
    """Processes all SF 330 PDF resumes in a given folder."""
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        print(f"Starting processing for: {pdf_path}")

        try:
            # ✅ Step 1: Upload PDF and get a signed URL
            pdf_url = upload_pdf_to_mistral(pdf_path)
            
            # ✅ Step 2: Extract structured JSON data from text
            structured_data = extract_structured_data_with_mistral(pdf_url)

            # ✅ Step 3: Store the extracted data in Pinecone
            employee_name = structured_data.get("Name", "Unknown")
            upsert_resume_in_pinecone(employee_name, pdf_url, structured_data)
        
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

# Example usage
if __name__ == "__main__":
    # Use the absolute path to the directory
    folder_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Section E Resumes")
    print(f"Looking for PDF files in: {folder_path}")
    process_section_e_pdfs(folder_path)

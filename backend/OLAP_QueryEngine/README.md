# PDF Processor for Supabase

This script processes PDF files, extracts text using OCR, chunks the content into sections, and uploads both the original PDF and its processed chunks to Supabase.

## Features

- PDF text extraction with PyMuPDF and OCR using pytesseract
- AI-powered text processing with Mistral AI (specifically version 1.6.0) with OpenAI as optional fallback
- Automatic chunking of PDF content into team/employee and project sections
- Supabase integration for storage and database operations
- Vector embeddings for semantic search capabilities
- Robust error handling and environment verification

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system
- Supabase account with storage bucket named "documents"
- MistralAI API key (compatible with Mistral AI 1.6.0)
- OpenAI API key (optional for fallback and embeddings)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
   Note: This will install Mistral AI 1.6.0 which is required for this application.

3. Install Tesseract OCR:
   - For macOS: `brew install tesseract`
   - For Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - For Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Configure your environment variables by editing the `.env` file in the root directory:
   ```
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_service_key
   
   # MistralAI Configuration
   MISTRAL_API_KEY=your_mistral_api_key
   MISTRAL_MODEL=mistral-large-latest
   
   # OpenAI Configuration (Optional fallback)
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```

## Usage

### Main Processing Script

Process a PDF file and upload to Supabase:

```bash
python pdf_processor.py /path/to/your/document.pdf
```

The script will:
1. Verify that the environment is properly configured
2. Check if the sample files mentioned in the requirements exist (not required to run)
3. Process the PDF file with Mistral AI 1.6.0
4. Upload the results to Supabase

### Test Script

For testing PDF extraction and AI processing without Supabase upload:

```bash
python test_pdf_extract.py /path/to/your/document.pdf
```

This will:
1. Extract text from the PDF and save it to a text file
2. Process the text with Mistral AI 1.6.0 and save the structured data to a JSON file
3. Display a summary of the extracted information

This test script is useful during development or when you want to verify the extraction works correctly before uploading to Supabase.

## Error Handling

The script includes robust error handling for:
- Missing PDF files
- Missing or invalid API credentials
- Tesseract OCR installation issues
- AI processing failures (with fallback options)
- Supabase connection or upload issues

## How It Works

1. **PDF Text Extraction**: The script extracts text from the PDF using PyMuPDF, falling back to OCR when needed.
2. **AI Processing**: The extracted text is processed using Mistral AI 1.6.0 to identify:
   - Team/employee information (name, role, full text)
   - Project information (name, location, full text)
3. **Chunking**: The content is chunked into separate sections:
   - One team/employee section
   - Multiple project sections
4. **Supabase Integration**:
   - The original PDF is uploaded to Supabase Storage
   - Extracted information is stored in the appropriate database tables
   - Relationships between teams, projects, and documents are created
   - Vector embeddings are generated for semantic search capabilities

## Database Schema

The script works with the following database schema:

- `teams`: Employee details (id, name, role, embedding)
- `projects`: Project details (id, name, location)
- `documents`: Document links (id, document_link, pdf_name)
- `sharded_documents`: Document chunks (text_id, document_id, text, embedding)
- `team_projects`: Links teams to projects
- `team_documents`: Links teams to documents
- `project_documents`: Links projects to documents 

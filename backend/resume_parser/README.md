# Resume Parser for Engiverse

A Python-based tool to extract structured data from SF 330 Section E resumes and store it in a Supabase vector database for powerful semantic search capabilities.

## Overview

This resume parser uses Mistral AI's OCR and language processing capabilities to extract detailed structured information from SF 330 Section E PDFs. The extracted data is normalized, validated, and stored in both local JSON files and a Supabase vector database for efficient retrieval and search.

## Features

- **PDF OCR Processing**: Uploads PDFs to Mistral AI for OCR text extraction
- **Structured Data Extraction**: Extracts detailed information including:
  - Personal details (name, role, years of experience)
  - Professional credentials (education, registrations)
  - Detailed project history with scope, costs, and responsibilities
- **Data Validation & Normalization**: Ensures consistent data formats
- **Duplicate Detection & Merging**: Intelligently combines data from multiple resume versions
- **Vector Embeddings**: Uses OpenAI's embedding models to create vector representations
- **Supabase Storage**: Stores extracted data and embeddings in Supabase for efficient retrieval
- **Semantic Search**: Query employees based on skills, experience, or project requirements

## Prerequisites

- Python 3.8+
- Mistral AI API key
- OpenAI API key
- Supabase project with vector search enabled

## Installation

1. Ensure you're using the project's virtual environment:

```bash
source backend/.venv/bin/activate
```

2. Install required packages:

```bash
pip install mistralai openai python-dotenv supabase
```

3. Configure environment variables (in .env file):

```
MISTRAL_API_KEY=your_mistral_api_key
OPENAI_API_KEY=your_openai_api_key
SUPABASE_PROJECT_URL=your_supabase_project_url
SUPABASE_PUBLIC_API_KEY=your_supabase_public_key
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
```

## Supabase Setup

1. In your Supabase project, navigate to the SQL Editor and run the provided `supabase_setup.sql` script. 
   This will:
   - Enable the vector extension
   - Create the `employees` table with vector embedding support
   - Set up the required search functions

Alternatively, you can execute these SQL statements manually:

```sql
CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE employees (
  id TEXT PRIMARY KEY,
  employee_name TEXT NOT NULL,
  file_id TEXT,
  resume_data JSONB NOT NULL,
  embedding VECTOR(1536) NOT NULL
);

-- Create an index on employee name for faster lookups
CREATE INDEX employees_name_idx ON employees (employee_name);
```

And create the vector search function:

```sql
CREATE OR REPLACE FUNCTION match_employees(
  query_embedding VECTOR(1536),
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id TEXT,
  employee_name TEXT,
  file_id TEXT,
  resume_data JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    employees.id,
    employees.employee_name,
    employees.file_id,
    employees.resume_data,
    1 - (employees.embedding <=> query_embedding) AS similarity
  FROM employees
  WHERE 1 - (employees.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
```

## Usage

### Processing PDFs

1. Place your SF 330 Section E PDF files in the `backend/Section E Resumes` directory 
   (this directory is created automatically when you run the setup script)

2. Run the parser:

```bash
cd backend
source .venv/bin/activate
python -m resume_parser.dataparser
```

The script will:
- Check multiple possible locations for the PDF files
- Create the directory if it doesn't exist
- Process all PDFs found in the directory
- Save the extracted data as JSON files
- Upload the data to Supabase with vector embeddings

### Troubleshooting PDF Location

If you encounter errors related to finding PDF files:

1. Ensure that you have placed PDF files in the correct directory
2. The script looks for PDFs in these locations (in order):
   - `backend/Section E Resumes`
   - `pdf_data/Section E Resumes`
   - `./Section E Resumes` (relative to current working directory)
   - `resume_parser/Section E Resumes`

3. If no directory is found, the script will create one at the current location

### Query Employees

You can query employees by skill, experience, or project requirements:

```python
from resume_parser.datauploader import query_employees

# Example: Find hydraulic engineers
results = query_employees("find hydraulic engineers with dam experience")

# Process results
for match in results:
    employee_data = match.get("resume_data", {})
    print(f"Employee: {employee_data.get('name')}")
    print(f"Similarity Score: {match.get('similarity'):.3f}")
    # Process other fields as needed
```

## Files

- `dataparser.py`: Main script for PDF processing and data extraction
- `datauploader.py`: Handles vector embedding generation and Supabase storage
- `README.md`: Documentation and usage instructions

## Best Practices

1. **Environment Variables**: Always keep API keys in the .env file
2. **Virtual Environment**: Use backend/.venv for all Python operations
3. **Batch Processing**: Process multiple PDFs in batches for efficiency
4. **Error Handling**: The system includes robust error handling to prevent failures

## Troubleshooting

- If OCR extraction is poor, ensure PDFs are high quality and text-searchable
- For embedding errors, check your OpenAI API key and rate limits
- If Supabase upserts fail, verify your table schema and API permissions

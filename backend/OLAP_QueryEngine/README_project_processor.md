# Project PDF Processor

This script processes project PDF documents and uploads them to Supabase with proper chunking and relationship linking.

## Overview

The `pdf_processor_projects.py` script is designed to:

1. Extract text from a project PDF document 
2. Identify and extract two specific chunks:
   - Project section (first section)
   - Firms section (from Section C)
3. Process these chunks with AI to extract structured data
4. Match firms mentioned in the document with existing teams in the database
5. Upload the original PDF and all extracted data to Supabase
6. Create appropriate relationships between projects, documents, and matching teams

## Usage

```
python pdf_processor_projects.py <pdf_path> [--skip-verify] [--use-mistral]
```

Arguments:
- `pdf_path`: Path to the project PDF file to process
- `--skip-verify`: (Optional) Skip environment verification
- `--use-mistral`: (Optional) Try using Mistral AI before OpenAI (if available)

## Chunking Logic

The script identifies sections in the PDF and extracts:
1. Project details from the first section (or Section F)
2. Firm information from Section C

This mirrors the example provided in `SectionF_Sections.pdf` where chunks are marked with a black box.

## Team Matching

The script checks if names of firms mentioned in the document match with team names in the Supabase `public.teams` table. If matches are found, it creates relationships between these teams and the extracted project.

## Database Structure

The script interacts with the following Supabase tables:
- `public.documents`: Stores information about the uploaded PDF
- `public.sharded_documents`: Stores extracted text chunks with embeddings
- `public.projects`: Stores project information
- `public.teams`: Used to match firm names with existing teams
- `public.team_projects`: Creates relationships between teams and projects
- `public.project_documents`: Links projects to their source documents

## Configuration

All configuration is stored in a single `.env` file in the root directory with the following variables:

```
# Supabase Configuration
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_key

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Mistral Configuration (Optional)
MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=mistral-small
```

## Error Handling

The script includes comprehensive error handling and logging to troubleshoot issues that may arise during processing. It also includes detailed environment verification to ensure all required components are properly configured before processing begins.

## Prerequisite Software

- Python 3.8+
- Tesseract OCR
- Required Python packages (specified in requirements.txt)

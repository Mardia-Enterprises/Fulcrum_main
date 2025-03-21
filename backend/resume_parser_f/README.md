# Section F Resume Parser

This module processes Section F resumes, extracts structured data using Mistral AI, and uploads the data with OpenAI embeddings to a Supabase database.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Data Structure](#data-structure)
- [Troubleshooting](#troubleshooting)

## Overview

The `resume_parser_f` module:

1. Processes Section F PDFs using Mistral AI for text extraction
2. Structures the data into specific JSON format with project details
3. Generates embeddings using OpenAI for semantic search
4. Uploads the structured data and embeddings to Supabase
5. Provides verification tools to ensure data integrity

## Setup

### Prerequisites

- Python 3.8 or higher
- Supabase account with a project set up
- Mistral AI API key
- OpenAI API key

### Installation

1. Ensure you have a `.env` file in the project root with the following keys:

```
MISTRAL_API_KEY=your_mistral_api_key
OPENAI_API_KEY=your_openai_api_key
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_key
```

2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Set up the Supabase database:

Run the SQL script in `supabase_setup.sql` in your Supabase SQL Editor to create the necessary tables and functions.

## Usage

### Process PDF files

```bash
cd backend/resume_parser_f
./process_section_f.sh
```

This script will:
- Look for PDF files in the `Section F Resumes` directory
- Process them with Mistral AI
- Generate structured JSON data
- Create embeddings with OpenAI
- Upload to Supabase

### Verify uploads

```bash
cd backend/resume_parser_f
python verify_uploads.py
```

This will check:
- If Supabase connection is working
- If the table structure is correct
- If permissions are properly set
- Test sample uploads and search functionality
- Display existing projects in the database

### Process a single project

```bash
cd backend/resume_parser_f
python process_projects.py --sample
```

This will process a sample project without needing to process PDFs, useful for testing.

## File Structure

- `dataparser.py`: Handles PDF extraction using Mistral AI
- `datauploader.py`: Manages embedding generation and Supabase uploads
- `process_projects.py`: Combines parsing and uploading in a single workflow
- `process_section_f.sh`: Shell script to handle the full processing pipeline
- `verify_uploads.py`: Verification script for Supabase data
- `supabase_setup.sql`: SQL setup script for Supabase
- `output/`: Directory for extracted JSON data
- `debug/`: Directory for debugging information

## Data Structure

The extracted data follows this JSON structure:

```json
{
  "project_owner": "USACE Fort Worth District",
  "year_completed": {
    "construction": null,
    "professional_services": 2019
  },
  "point_of_contact": "555-555-5555",
  "brief_description": "Project description text...",
  "title_and_location": "Project Title, Location",
  "firms_from_section_c": [
    {
      "role": "Prime: Architecture, Civil, Structural, and MEP",
      "firm_name": "Example Engineering",
      "firm_location": "City, State"
    },
    {
      "role": "Sub: Civil, Structural, and ITR",
      "firm_name": "Another Firm Inc.",
      "firm_location": "Other City, ST"
    }
  ],
  "point_of_contact_name": "Contact Name, Role"
}
```

## Troubleshooting

### Common Issues

1. **PDF extraction fails**:
   - Check that the Mistral API key is correct
   - Ensure PDFs are properly formatted SF330 Section F forms
   - Look at the log file for detailed error messages

2. **Embedding generation fails**:
   - Verify the OpenAI API key is correct
   - Check OpenAI usage limits and billing status

3. **Supabase uploads fail**:
   - Ensure the Supabase URL and API key are correct
   - Check that the `projects` table is created with the correct structure
   - Verify that the pgvector extension is enabled

4. **Missing fields in extracted data**:
   - Check the PDFs for correct formatting
   - Look at the generated JSON files in the `output/` directory
   - May require manual correction of the JSON data

### Logs

Check `resume_parser.log` for detailed logs of the extraction and upload process.

### Running Verification

Always run `verify_uploads.py` after setting up the system to ensure everything is configured correctly.

### Error Handling

The system has built-in error handling with:
- Rate limit handling for API calls
- Exponential backoff for retries
- Detailed logging
- Exception handling for all critical operations 
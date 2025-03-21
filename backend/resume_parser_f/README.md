# Section F Resume Parser

This module processes Section F PDFs containing project information and uploads the structured data to Supabase.

## Prerequisites

The following dependencies are required:
- Python 3.8+
- mistralai==0.4.2 (important: must use version 0.4.2 specifically)
- openai
- supabase
- pdfplumber
- python-dotenv

## Installation

1. Make sure you have a proper `.env` file in the root directory of the project with the following variables:
   ```
   MISTRAL_API_KEY=your_mistral_api_key
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_PROJECT_URL=your_supabase_url
   SUPABASE_PRIVATE_API_KEY=your_supabase_key
   ```

2. Install the required dependencies:
   ```bash
   ./install_dependencies.sh
   ```

## Usage

To process PDFs in the Section F Resumes directory:

```bash
./process_section_f.sh
```

This will:
1. Check if all required environment variables are set
2. Import required dependencies
3. Process all PDFs in the Section F Resumes directory
4. Extract structured data using Mistral AI
5. Upload the data to Supabase

## Handling Duplicates

The system now includes duplicate detection and prevention:

1. **Prevention:** When processing new PDFs, the system checks for existing projects with similar titles before creating new entries. If a similar project is found, it will update the existing project instead of creating a duplicate.

2. **Cleanup:** To clean up existing duplicates in the database, run:
   ```bash
   ./cleanup_duplicates.py
   ```
   
   This script will:
   - Identify groups of duplicates based on title similarity
   - Merge the data from all duplicates into the most recent one
   - Update the primary project with the merged data
   - Delete the duplicate entries
   
   The script has a "dry run" option that shows what would be changed without making actual changes.

## Troubleshooting

If you encounter an error like this:
```
Error: Failed to import Mistral AI client. Please install with 'pip install mistralai'
```

Run the installation script:
```bash
./install_dependencies.sh
```

### Mistral API Version Issue

The code requires mistralai version 0.4.2 specifically. Newer versions (1.x+) use a different API that is not compatible with the current code.

If you see an error like this:
```
This client is deprecated. To migrate to the new client, please refer to this guide: https://github.com/mistralai/client-python/blob/main/MIGRATION.md
```

Run the fix script:
```bash
python3 fix_mistral_version.py
```

This will downgrade mistralai to version 0.4.2.

### Compatibility Layer

The code includes a compatibility layer (`mistral_compat.py`) that allows it to work with both the old v0.4.2 API and newer versions. This ensures that features like file upload, which were introduced in newer versions, still work even when using v0.4.2.

When using v0.4.2, the compatibility layer extracts text from PDF files locally using pdfplumber instead of using the file upload API.

### Fixed Issues

The following issues have been fixed in the current version:
- ChatMessage error fixed by using dictionaries instead of ChatMessage objects
- Timestamp variable access error fixed in the JSON parsing code
- Title processing error fixed by ensuring titles are always strings
- Supabase table not found error now handled gracefully with appropriate messages

### Supabase Integration

The script will attempt to upload data to Supabase. If the "projects" table doesn't exist in your Supabase database, you need to create it with the following columns:
- id (text, primary key)
- title (text)
- project_data (jsonb)
- embedding (vector(1536))

If you don't have access to Supabase, the script will still extract data from the PDFs and save it as JSON files in the output directory.

## Files

- `process_section_f.sh`: Main script to process PDFs
- `process_projects.py`: Python script that orchestrates the PDF processing workflow
- `dataparser.py`: Handles PDF parsing and extraction of structured data
- `datauploader.py`: Uploads extracted data to Supabase
- `install_dependencies.sh`: Installs required dependencies
- `mistral_compat.py`: Compatibility layer for Mistral API versions 
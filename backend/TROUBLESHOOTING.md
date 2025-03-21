# Troubleshooting Guide

This document provides detailed instructions for troubleshooting common issues with the PDF parsing and project data management system.

## Table of Contents
- [Environment Setup Issues](#environment-setup-issues)
- [Supabase Connection Issues](#supabase-connection-issues)
- [Mistral API Issues](#mistral-api-issues)
- [OpenAI API Issues](#openai-api-issues)
- [PDF Processing Issues](#pdf-processing-issues)
- [Data Format Issues](#data-format-issues)
- [Vector Dimension Issues](#vector-dimension-issues)
- [Comprehensive Debugging](#comprehensive-debugging)

## Environment Setup Issues

### Virtual Environment Problems

**Symptoms**: Scripts fail with Python import errors, or the wrong Python version is used.

**Solutions**:

1. Ensure the virtual environment is created correctly:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Verify the correct Python version:
   ```bash
   python --version  # Should be 3.8 or higher
   ```

3. Run the environment setup script:
   ```bash
   ./setup_environment.sh
   ```

4. If you're experiencing dependency issues, use the dedicated installer:
   ```bash
   ./install_dependencies.sh
   ```

### Environment Variables

**Symptoms**: "API key not found" errors, or authentication failures.

**Solutions**:

1. Ensure `.env` file exists in the root directory with these variables:
   ```
   MISTRAL_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   SUPABASE_PROJECT_URL=your_url_here
   SUPABASE_PRIVATE_API_KEY=your_key_here
   ```

2. Check the `.env` file is being loaded:
   ```bash
   cd backend
   python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print(os.getenv('MISTRAL_API_KEY')[:4] + '...')"
   ```

## Supabase Connection Issues

### Connection Failures

**Symptoms**: "Cannot connect to Supabase" errors or "Table not found" errors.

**Solutions**:

1. Run the Supabase diagnostic tool:
   ```bash
   cd backend
   ./debug_supabase.py
   ```

2. Check your Supabase URL and API key:
   - Ensure the `SUPABASE_PROJECT_URL` is formatted as `https://your-project-id.supabase.co`
   - Verify the `SUPABASE_PRIVATE_API_KEY` is the correct service role key from Supabase dashboard

3. Check if the `projects` table exists:
   ```bash
   cd backend
   python -c "
   import os
   from dotenv import load_dotenv
   from supabase import create_client
   load_dotenv('../.env')
   supabase = create_client(os.getenv('SUPABASE_PROJECT_URL'), os.getenv('SUPABASE_PRIVATE_API_KEY'))
   try:
       result = supabase.table('projects').select('id').limit(1).execute()
       print('Table exists:', result.data)
   except Exception as e:
       print('Error:', str(e))
   "
   ```

### Database Structure Issues

**Symptoms**: Projects are not being inserted, or "column does not exist" errors.

**Solutions**:

1. Run the SQL setup script from the `resume_parser_f/supabase_setup.sql` file in your Supabase SQL Editor.

2. Check the table structure:
   ```bash
   cd backend/resume_parser_f
   python -c "
   import os
   from dotenv import load_dotenv
   from supabase import create_client
   load_dotenv('../../.env')
   supabase = create_client(os.getenv('SUPABASE_PROJECT_URL'), os.getenv('SUPABASE_PRIVATE_API_KEY'))
   try:
       result = supabase.table('projects').select('*').limit(1).execute()
       if result.data:
           print('Table fields:', list(result.data[0].keys()))
       else:
           print('Table is empty')
   except Exception as e:
       print('Error:', str(e))
   "
   ```

## Mistral API Issues

### API Key Issues

**Symptoms**: "Invalid API key" errors or failures to extract data from PDFs.

**Solutions**:

1. Run the Mistral debug script:
   ```bash
   cd backend
   ./debug_mistral.py
   ```

2. Verify your API key:
   - Check if it's correctly set in the `.env` file
   - Try to use the key directly on the Mistral API dashboard

### API Version Issues

**Symptoms**: Import errors like `No module named 'mistralai.exceptions'` or errors in API calls.

**Solutions**:

1. Update the Mistral package to the latest version:
   ```bash
   cd backend
   source .venv/bin/activate
   pip install --upgrade mistralai
   ```

2. Ensure your code is using the latest API format:
   - The latest version uses `MistralClient` instead of `Mistral`
   - API calls should use the appropriate format for your version

3. Check the Mistral client version:
   ```bash
   cd backend
   source .venv/bin/activate
   python -c "import mistralai; print(mistralai.__version__)"
   ```

4. Install all dependencies properly:
   ```bash
   cd backend
   ./install_dependencies.sh
   ```

### Rate Limit Issues

**Symptoms**: "Rate limit exceeded" errors or processing stopping after a few PDFs.

**Solutions**:

1. Introduce delays between PDF processing:
   - The default script now includes exponential backoff for rate limits
   - Process fewer PDFs at a time

2. Monitor API usage on the Mistral dashboard

3. Check the retry settings in `dataparser.py`:
   ```python
   # Higher values for max_retries and base_delay will handle rate limits better
   extract_structured_data_with_mistral(url, max_retries=5, base_delay=2)
   ```

## OpenAI API Issues

### Embedding Generation Issues

**Symptoms**: "Failed to generate embedding" errors or projects stored without proper embeddings.

**Solutions**:

1. Check your OpenAI API key:
   ```bash
   cd backend
   python -c "
   import os
   from dotenv import load_dotenv
   from openai import OpenAI
   load_dotenv('../.env')
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   try:
       models = client.models.list()
       print('OpenAI connection successful')
   except Exception as e:
       print('Error:', str(e))
   "
   ```

2. Test embedding generation:
   ```bash
   cd backend
   python -c "
   import os
   from dotenv import load_dotenv
   from openai import OpenAI
   load_dotenv('../.env')
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   try:
       response = client.embeddings.create(input='Test embedding', model='text-embedding-3-small')
       embedding = response.data[0].embedding
       print(f'Successfully generated embedding with {len(embedding)} dimensions')
   except Exception as e:
       print('Error:', str(e))
   "
   ```

## PDF Processing Issues

### PDF Not Found

**Symptoms**: "No PDF files found" warnings or empty processing results.

**Solutions**:

1. Check the PDF directory:
   ```bash
   ls -la "Section F Resumes"
   ```

2. Ensure PDFs are properly formatted SF 330 Section F forms

3. Try processing a specific PDF manually:
   ```bash
   cd backend
   ./test_pdf_processing.py --pdf="path/to/your/file.pdf"
   ```

### Extraction Failures

**Symptoms**: Empty or incomplete JSON data extracted from PDFs.

**Solutions**:

1. Check the PDF quality:
   - Ensure it's not password-protected
   - Check if it's a scanned document (may require OCR)
   - Verify it's a properly formatted SF 330 Section F form

2. Test the Mistral API directly:
   ```bash
   cd backend
   ./debug_mistral.py
   ```

3. Examine logs for specific error messages:
   ```bash
   cat resume_parser.log
   ```

## Data Format Issues

### Incomplete Project Data

**Symptoms**: Projects missing required fields or incomplete data in Supabase.

**Solutions**:

1. Run the verification script:
   ```bash
   cd backend/resume_parser_f
   python verify_uploads.py
   ```

2. Check the generated JSON files:
   ```bash
   ls -la resume_parser_f/output/
   ```

3. Examine the extracted data structure:
   ```bash
   cd backend
   python -c "
   import json
   import glob
   files = glob.glob('resume_parser_f/output/*.json')
   if files:
       with open(files[0]) as f:
           data = json.load(f)
           print('Fields:', list(data.keys()))
           print('Missing required fields:', [f for f in ['title_and_location', 'year_completed', 'project_owner', 'point_of_contact_name', 'point_of_contact', 'brief_description', 'firms_from_section_c'] if f not in data])
   else:
       print('No JSON files found')
   "
   ```

## Vector Dimension Issues

### Dimension Mismatch Errors

**Symptoms**: Errors like `expected 1536 dimensions, not X` when inserting data into Supabase.

**Solutions**:

1. Check your table setup in Supabase:
   - Ensure the `embedding` column is defined as `vector(1536)` to match OpenAI embeddings

2. Check the embedding dimensions in debug scripts:
   - Edit the `debug_supabase.py` script and ensure test data uses full-size vectors:
     ```python
     'embedding': [0.1] * 1536  # Must be exactly 1536 dimensions
     ```

3. Update the Supabase table definition:
   ```sql
   ALTER TABLE projects 
   DROP COLUMN IF EXISTS embedding;
   
   ALTER TABLE projects 
   ADD COLUMN embedding vector(1536);
   ```

4. Verify that embeddings are being generated with the correct dimensions:
   ```bash
   cd backend
   python -c "
   import os
   from dotenv import load_dotenv
   from openai import OpenAI
   load_dotenv('../.env')
   client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
   response = client.embeddings.create(input='Test embedding', model='text-embedding-3-small')
   embedding = response.data[0].embedding
   print(f'Embedding dimensions: {len(embedding)}')
   "
   ```

## Comprehensive Debugging

For a complete diagnostic of the entire system, run the following tools:

1. **Supabase diagnostics**:
   ```bash
   cd backend
   ./debug_supabase.py
   ```

2. **Mistral API diagnostics**:
   ```bash
   cd backend
   ./debug_mistral.py
   ```

3. **Full PDF processing test**:
   ```bash
   cd backend
   ./test_pdf_processing.py
   ```

4. **Verify uploads**:
   ```bash
   cd backend/resume_parser_f
   python verify_uploads.py
   ```

5. **Process and monitor**:
   ```bash
   cd backend
   ./process_projects.sh
   ```

These diagnostic tools will provide detailed information about any issues in the system and guide you toward the appropriate solutions.

## Additional Resources

- **Logs**: Check `resume_parser.log` and `pdf_processing_test.log` for detailed error messages
- **JSON outputs**: Examine files in `resume_parser_f/output/` for extracted data
- **Debug data**: Look in `resume_parser_f/debug/` for debugging information

If you continue to experience issues after following these troubleshooting steps, please reach out for additional support. 
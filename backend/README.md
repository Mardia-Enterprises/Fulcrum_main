# Project Profiles Backend

This backend system processes SF 330 Section F project profiles and provides an API for searching and retrieving project data.

## Components

1. **resume_parser_f**: PDF processing module that extracts structured data from Section F project profiles
2. **API_projects**: FastAPI-based REST API for project data management and search

## Setup

### Environment Setup

1. Run the setup script to prepare your environment:

```bash
cd backend
./setup_environment.sh
```

This script will:
- Create or update the virtual environment in `.venv`
- Install all required dependencies
- Create a template `.env` file if one doesn't exist
- Set up necessary directories

2. Edit the `.env` file in the project root with your API keys:

```
# API Keys
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key

# Supabase Configuration
SUPABASE_PROJECT_URL=your_supabase_project_url
SUPABASE_PRIVATE_API_KEY=your_supabase_api_key

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8001
```

### Database Setup

1. Set up the Supabase database by running the SQL in `resume_parser_f/supabase_setup.sql`

2. The SQL script will:
   - Create the `projects` table with the correct structure
   - Set up vector search functionality
   - Create necessary indexes for performance

### Processing PDF Files

1. Place your SF 330 Section F PDF files in the `backend/Section F Resumes` directory

2. Process the PDF files and upload the data to Supabase:

```bash
cd backend
./process_projects.sh
```

3. The script will:
   - Activate the virtual environment
   - Extract data from all PDFs using Mistral AI
   - Upload the structured data to Supabase with embeddings
   - Run the repair script to ensure all data is properly structured

### Running the API

1. Start the API server:

```bash
cd backend
./run_api.sh
```

2. The API will be available at `http://localhost:8001` (or the port specified in your `.env` file)

## Troubleshooting

### Database Issues

If you encounter issues with the Supabase database, run the debug script:

```bash
cd backend
./debug_supabase.py
```

This will:
- Test the database connection
- Check the table structure
- Examine project data format
- Provide helpful tips for fixing common issues

### PDF Processing Issues

If you encounter issues with PDF processing or the Mistral API, run the debug script:

```bash
cd backend
./debug_mistral.py
```

This will:
- Test the Mistral API connection
- Verify PDF upload functionality
- Test basic text extraction
- Provide troubleshooting tips

### Data Structure Issues

If project data is missing fields or improperly formatted, run the repair script:

```bash
cd backend
source .venv/bin/activate
cd API_projects
python repair_projects.py
```

## API Documentation

When the API is running, visit `http://localhost:8001/docs` for the interactive API documentation.

For more details about the API, see the [API_projects README](API_projects/README.md).

## Updating

To update dependencies, run:

```bash
cd backend
./setup_environment.sh
```

And choose 'y' when asked if you want to upgrade the existing environment.

# Fulcrum Backend

This is the backend system for the Fulcrum application. It consists of various modules for data processing and API services.

## Environment Configuration

**IMPORTANT**: The system uses a single `.env` file located in the **root directory** of the project (one level up from the backend folder). All API keys and configuration settings should be placed in this file.

Example `.env` file in the root directory:
```
MISTRAL_API_KEY=your_mistral_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_PROJECT_URL=your_supabase_url_here
SUPABASE_PRIVATE_API_KEY=your_supabase_key_here
API_PORT=8000
API_HOST=0.0.0.0
DEBUG=True
```

Do not create additional `.env` files in subdirectories. All scripts are configured to use only the root `.env` file.

## Processing Section F Resumes

The system is set up to process resumes from the `Section F Resumes` directory. Here's how to use it:

1. Place your PDF files in the `backend/Section F Resumes` directory.
2. Ensure your environment variables are set in the `.env` file in the **root directory**.
3. Run the processing script:

```bash
cd backend
./process_section_f.sh
```

This will:
- Process all PDF files in the `Section F Resumes` directory
- Extract structured data using Mistral AI
- Generate embeddings using OpenAI
- Upload the data to Supabase

## Directory Structure

```
project_root/
├── .env                      # SINGLE .env file for all configuration
├── backend/
│   ├── Section F Resumes/    # Place PDF files here for processing
│   │   └── SectionF.pdf      # Example PDF file
│   ├── process_section_f.sh  # Main script to process PDFs
│   ├── resume_parser_f/      # PDF processing module
│   │   ├── dataparser.py     # Extracts data from PDFs using Mistral AI
│   │   ├── datauploader.py   # Uploads data to Supabase with embeddings
│   │   ├── datauploader_fix.py # Fixes embedding dimension issues
│   │   ├── direct_pdf_processor.py # Direct processor without sample data
│   │   ├── execute_processor.sh # Shell script to execute the processor
│   │   └── supabase_setup.sql # SQL setup for Supabase
│   └── [other directories...]
```

## Troubleshooting

If you encounter issues:

1. Verify that your `.env` file is in the root directory (not in the backend folder).

2. Check the log files:
   - `backend/resume_parser_f/direct_pdf_processor.log`
   - `backend/resume_parser_f/resume_parser.log`

3. Run the embedding dimension fix:
   ```bash
   cd backend/resume_parser_f
   ./datauploader_fix.py
   ```

4. Make sure your `.env` file has valid API keys.

5. Ensure that the Supabase database is properly set up with the SQL in `resume_parser_f/supabase_setup.sql`.

## API Documentation

Once the API is running, you can access the Swagger documentation at:
http://localhost:8000/docs

The API provides endpoints for:

- Searching projects semantically (`/api/projects/search`)
- Dedicated endpoint for owner search (`/api/projects/search-by-owner`)
- Managing project data (CRUD operations)
- Repairing and updating project structures

## Updating Dependencies

If you need to update dependencies:

1. Edit the `requirements.txt` file
2. Run:

```bash
source .venv/bin/activate
pip install -r requirements.txt
``` 
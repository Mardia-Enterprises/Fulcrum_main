# Project Profiles API

A FastAPI-based REST API for managing and querying project profiles with semantic search capabilities.

## Overview

This API provides endpoints for:

1. Retrieving a list of all projects
2. Getting detailed information about a specific project
3. Creating new projects
4. Updating existing projects
5. Deleting projects
6. Querying projects using semantic search
7. Searching projects by owner with enhanced text matching

## Dependencies

- FastAPI
- Uvicorn
- Supabase Python client
- OpenAI Python client (for embeddings)
- Python-dotenv

## Setup

1. Make sure your root `.env` file contains the required environment variables:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_PROJECT_URL=your_supabase_project_url
SUPABASE_PRIVATE_API_KEY=your_supabase_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

2. The project uses the existing `.venv` virtual environment in the backend folder. If you need to install dependencies, activate the virtual environment first:

```bash
cd backend
source .venv/bin/activate
pip install fastapi uvicorn supabase openai python-dotenv mistralai
```

3. Make sure you've set up the Supabase database with the projects table as described in `resume_parser_f/supabase_setup.sql`.

## Running the API

Use the shell script to run the API using the existing virtual environment:

```bash
cd backend
./run_api.sh
```

Alternatively, you can run it manually:

```bash
cd backend
source .venv/bin/activate
cd API_projects
python run_api.py
```

The API will be available at `http://localhost:8001`.

## Processing PDF Files

To process Section F PDF files and update the Supabase database:

```bash
cd backend
./process_projects.sh
```

This script will:
1. Activate the `.venv` virtual environment
2. Process all PDFs in the Section F folder
3. Run the repair script to ensure all data is in the correct format
4. Deactivate the virtual environment when completed

## API Endpoints

### Get All Projects

```
GET /api/projects
```

Returns a list of all projects with basic information.

### Get Project Details

```
GET /api/projects/{project_id}
```

Returns detailed information about a specific project.

### Create Project

```
POST /api/projects
```

Creates a new project. Request body should follow the ProjectCreate model.

### Update Project

```
PUT /api/projects/{project_id}
```

Updates an existing project. Request body should follow the ProjectUpdate model.

### Delete Project

```
DELETE /api/projects/{project_id}
```

Deletes a project by ID.

### Query Projects

```
POST /api/projects/query
```

Performs semantic search on projects. Request body should follow the QueryRequest model:

```json
{
  "query": "flood control projects in Texas",
  "limit": 10
}
```

### Search Projects by Owner

```
GET /api/projects/owner/{owner_text}?limit=10
```

Searches for projects with a specific owner or client, with fuzzy matching for common variations.
This endpoint is particularly useful for finding USACE projects and handles common abbreviations.

Example: `/api/projects/owner/USACE`

## Search Features

This API implements several search strategies for finding projects:

1. **Direct Owner Text Search**: First attempts to find projects by direct text matching against owner fields
2. **OpenAI Semantic Search**: Uses OpenAI embeddings for semantic similarity search
3. **Fuzzy Text Matching**: Handles abbreviations, variations, and partial word matches
4. **Fallback Search**: Falls back to vector search implementation from resume_parser_f if needed

## Data Models

### Project Detail

```json
{
  "id": "granger_lake_management_office_building_design_granger_tx",
  "title_and_location": "Granger Lake Management Office Building Design, Granger, TX",
  "year_completed": {
    "professional_services": "2019",
    "construction": "2021"
  },
  "project_owner": "USACE Fort Worth District",
  "point_of_contact_name": "Sharon Leheny, Project Manager",
  "point_of_contact": "817-886-1563",
  "brief_description": "Detailed project description...",
  "firms_from_section_c": [
    {
      "firm_name": "MSMM Engineering",
      "firm_location": "New Orleans, LA",
      "role": "Prime: Architecture, Civil, Structural, and MEP"
    }
  ]
}
```

## Integration with resume_parser_f

This API uses the embedding and storage functionality from `resume_parser_f.datauploader` to generate vector embeddings and perform semantic search on project profiles. 

## Data Structure Issues

If you encounter issues with incomplete project data structures, you can run the repair script:

```bash
cd backend/API_projects
python repair_projects.py
```

This will validate all projects in the database and fix any structural issues with missing fields or incorrect data types.

## Troubleshooting

### Missing Fields in Project Data

Each project must have the following fields:

```json
{
  "id": "project_identifier",
  "title_and_location": "Project Title and Location",
  "year_completed": {
    "professional_services": 2019,
    "construction": 2021
  },
  "project_owner": "USACE Fort Worth District",
  "point_of_contact_name": "John Doe, Project Manager",
  "point_of_contact": "555-555-5555",
  "brief_description": "Detailed project description...",
  "firms_from_section_c": [
    {
      "firm_name": "MSMM Engineering",
      "firm_location": "New Orleans, LA",
      "role": "Prime: Architecture, Civil, Structural, and MEP"
    },
    {
      "firm_name": "Huitt-Zollars, Inc.",
      "firm_location": "Fort Worth, TX",
      "role": "Sub: Civil, Structural, and ITR"
    }
  ]
}
```

If any fields are missing when creating or retrieving projects, the API will attempt to provide default values to maintain the structure. If you're still experiencing issues, run the repair script mentioned above. 
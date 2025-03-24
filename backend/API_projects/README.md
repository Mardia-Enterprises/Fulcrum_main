# Project API

This API provides endpoints for querying and managing project data stored in Supabase.

## Overview

The API allows you to:
- Search for projects using natural language queries
- Retrieve project details
- Add new projects (both via file upload or manual entry)
- Update existing projects
- Merge projects
- Delete projects

The project data is stored in Supabase using vector embeddings for semantic search capabilities.

## Setup

1. Ensure the backend virtual environment is activated:

```bash
cd backend
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows
```

2. Install the required dependencies:

```bash
pip install -r API_projects/requirements.txt
```

3. Make sure the root `.env` file in the project root directory contains the following variables:

```
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
```

## Running the API

Start the API server:

```bash
cd backend
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows
cd API_projects
python run_api.py
```

The API will be available at http://localhost:8001

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Endpoints

### 1. Query Projects

Search for projects based on a natural language query.

- **URL**: `/api/query`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "water treatment projects in Texas"
  }
  ```

### 2. List All Projects

Get a list of all projects.

- **URL**: `/api/projects`
- **Method**: `GET`

### 3. Get Project Details

Get detailed information about a specific project.

- **URL**: `/api/projects/{project_title}`
- **Method**: `GET`

### 4. Add Project via File Upload

Add a new project by uploading a PDF file.

- **URL**: `/api/projects`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF file (required)
  - `project_title`: Project title (optional, will use filename if not provided)

### 5. Add Project Manually

Add a new project by providing structured data manually.

- **URL**: `/api/projects/manual`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "title_and_location": "Water Treatment Plant, Austin TX",
    "year_completed": {
      "professional_services": 2020,
      "construction": 2022
    },
    "project_owner": "City of Austin",
    "point_of_contact_name": "John Smith, Project Manager",
    "point_of_contact_telephone_number": "512-555-1234",
    "brief_description": "Design and construction of a 5 MGD water treatment plant...",
    "firms_from_section_c_involved_with_this_project": [
      {
        "firm_name": "Engineering Firm Inc.",
        "firm_location": "Austin, TX",
        "role": "Prime: Civil and Structural"
      }
    ]
  }
  ```

### 6. Update Project

Update an existing project by providing new data.

- **URL**: `/api/projects/{project_title}`
- **Method**: `PUT`
- **Content-Type**: `application/json`
- **Request Body**: Same as "Add Project Manually"

### 7. Merge Projects

Merge two projects, combining their information.

- **URL**: `/api/merge_projects`
- **Method**: `POST`
- **Query Parameters**:
  - `source_title`: The title of the source project
  - `target_title`: The title of the target project

### 8. Delete Project

Delete a project by title.

- **URL**: `/api/projects/{project_title}`
- **Method**: `DELETE`

### Import Projects from Employee Data

The API includes endpoints to import projects from employee data stored in the Employee API:

#### Import Projects from a Specific Employee

```
POST /api/projects_from_employee_api/{employee_name}
```

This endpoint retrieves an employee from the Employees API and imports all of their projects into the Projects database. The projects will include information such as:
- Title and location
- Project fee and cost (if available)
- Project owner (if available) 
- Project scope as the brief description
- The employee's role in the project
- The employee's firm information

**Response**:
```json
{
  "status": "success",
  "projects_imported": [
    {
      "project_id": "project_title_location",
      "title": "Project Title, Location"
    },
    ...
  ]
}
```

#### Import Projects from All Employees

```
POST /api/projects_from_all_employees
```

This endpoint iterates through all employees in the Employees API and imports their projects into the Projects database.

**Response**:
```json
{
  "status": "success",
  "total_projects_imported": 42,
  "summary": {
    "Employee Name 1": 3,
    "Employee Name 2": 5,
    ...
  }
}
```

These endpoints are complementary to similar endpoints in the Employees API, providing a way to sync project data between both APIs.

## Example Usage

### Query for Projects

```bash
curl -X 'POST' \
  'http://localhost:8001/api/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "water treatment projects in Texas"
}'
```

### Upload a Project PDF

```bash
curl -X 'POST' \
  'http://localhost:8001/api/projects' \
  -H 'accept: application/json' \
  -F 'file=@/path/to/project.pdf' \
  -F 'project_title=Water Treatment Plant'
```

### Add a Project Manually

```bash
curl -X 'POST' \
  'http://localhost:8001/api/projects/manual' \
  -H 'Content-Type: application/json' \
  -d '{
  "title_and_location": "Water Treatment Plant, Austin TX",
  "year_completed": {
    "professional_services": 2020,
    "construction": 2022
  },
  "project_owner": "City of Austin",
  "point_of_contact_name": "John Smith, Project Manager",
  "point_of_contact_telephone_number": "512-555-1234",
  "brief_description": "Design and construction of a 5 MGD water treatment plant...",
  "firms_from_section_c_involved_with_this_project": [
    {
      "firm_name": "Engineering Firm Inc.",
      "firm_location": "Austin, TX",
      "role": "Prime: Civil and Structural"
    }
  ]
}'
```

### Delete a Project

```bash
curl -X 'DELETE' \
  'http://localhost:8001/api/projects/Water%20Treatment%20Plant%2C%20Austin%20TX'
```

## Database Structure

The API uses Supabase as the vector database for storing project data. The main table is `section_f_projects` with the following structure:

- `id`: TEXT (primary key, derived from project title)
- `project_key`: TEXT (full title of the project)
- `file_id`: TEXT (identifier for the uploaded file)
- `project_data`: JSONB (structured data extracted from the PDF)
- `embedding`: VECTOR(1536) (vector embedding for semantic search) 
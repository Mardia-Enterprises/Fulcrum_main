# Employee Resume API

This API provides endpoints for querying and managing employee resume data stored in Supabase.

## Overview

The API allows you to:
- Search for employees using natural language queries
- Retrieve employee details
- Add new employees (both via file upload or manual entry)
- Delete employees

The employee data is stored in Supabase using vector embeddings for semantic search capabilities.

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
pip install -r API/requirements.txt
```

3. Make sure the root `.env` file in the project root directory contains the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
```

4. Verify your Supabase connection:

Before running the API, you can verify that your connection to Supabase is working and that the necessary tables and functions exist:

```bash
cd backend
source .venv/bin/activate  # On Unix/macOS
cd API
python check_connection.py
```

If the script reports any issues, follow the provided instructions to set up your Supabase database correctly.

## Running the API

Start the API server:

```bash
cd backend
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate     # On Windows
cd API
python run_api.py
```

Alternatively, you can use uvicorn directly (but this might cause import issues):

```bash
cd backend
source .venv/bin/activate  # On Unix/macOS
cd API
python -m uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### 1. Query Employees

Search for employees based on a natural language query.

- **URL**: `/api/query`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "hydraulic engineers with experience in flood control"
  }
  ```

### 2. List All Employees

Get a list of all employees.

- **URL**: `/api/employees`
- **Method**: `GET`

### 3. Get Employee Details

Get detailed information about a specific employee.

- **URL**: `/api/employees/{employee_name}`
- **Method**: `GET`

### 4. Get Employees by Role

Get all employees with a specific role.

- **URL**: `/api/roles/{role}`
- **Method**: `GET`

### 5. Add Employee via File Upload

Add a new employee by uploading their resume PDF.

- **URL**: `/api/employees`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF file (required)
  - `employee_name`: Employee name (optional, will use filename if not provided)

### 6. Add Employee Manually

Add a new employee by providing structured data manually.

- **URL**: `/api/employees/manual`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "role": "Civil Engineer",
    "years_experience": {
      "Total": "15 years",
      "With Current Firm": "5 years"
    },
    "firm": {
      "Name": "Engineering Firm Inc.",
      "Location": "New York, NY"
    },
    "education": "Bachelor of Engineering, Civil Engineering, MIT",
    "professional_registrations": [
      {
        "State": "New York",
        "License": "PE12345"
      }
    ],
    "other_qualifications": "PMP Certified",
    "relevant_projects": [
      {
        "Title and Location": "Bridge Construction, Boston, MA",
        "Description": "Design and construction oversight of a 500-foot suspension bridge",
        "Role": "Lead Engineer",
        "Fee": "$1.5M"
      }
    ]
  }
  ```

### 7. Delete Employee

Delete an employee by name.

- **URL**: `/api/employees/{employee_name}`
- **Method**: `DELETE`

## Example Usage

### Query for Employees

```bash
curl -X 'POST' \
  'http://localhost:8000/api/query' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "hydraulic engineers with experience in flood control"
}'
```

### Upload a Resume

```bash
curl -X 'POST' \
  'http://localhost:8000/api/employees' \
  -H 'accept: application/json' \
  -F 'file=@/path/to/resume.pdf' \
  -F 'employee_name=John Doe'
```

### Add an Employee Manually

```bash
curl -X 'POST' \
  'http://localhost:8000/api/employees/manual' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "John Doe",
  "role": "Civil Engineer",
  "years_experience": {
    "Total": "15 years",
    "With Current Firm": "5 years"
  },
  "firm": {
    "Name": "Engineering Firm Inc.",
    "Location": "New York, NY"
  },
  "education": "Bachelor of Engineering, Civil Engineering, MIT",
  "professional_registrations": [
    {
      "State": "New York",
      "License": "PE12345"
    }
  ],
  "other_qualifications": "PMP Certified",
  "relevant_projects": [
    {
      "Title and Location": "Bridge Construction, Boston, MA",
      "Description": "Design and construction oversight of a 500-foot suspension bridge",
      "Role": "Lead Engineer",
      "Fee": "$1.5M"
    }
  ]
}'
```

### Delete an Employee

```bash
curl -X 'DELETE' \
  'http://localhost:8000/api/employees/John%20Doe'
```

## Database Structure

The API uses Supabase as the vector database for storing employee resume data. The main table is `employees` with the following structure:

- `id`: TEXT (primary key, derived from employee name)
- `employee_name`: TEXT (full name of the employee)
- `file_id`: TEXT (identifier for the uploaded file)
- `resume_data`: JSONB (structured data extracted from the resume)
- `embedding`: VECTOR(1536) (vector embedding of the resume data)

The resume_data field contains the following structure:
```json
{
  "Name": "Employee's full name",
  "Role in Contract": "Employee's role",
  "Years of Experience": {
    "Total": "X years",
    "With Current Firm": "Y years"
  },
  "Firm Name & Location": {
    "Name": "Company name",
    "Location": "Company location"
  },
  "Education": "Education details",
  "Professional Registrations": [
    {
      "State": "State name",
      "License": "License details"
    }
  ],
  "Other Professional Qualifications": "Other qualifications",
  "Relevant Projects": [
    {
      "Title and Location": "Project name",
      "Description": "Project description",
      "Role": "Employee's role in the project",
      "Fee": "Project fee"
    }
  ]
}
```

## Environment Variables

All environment variables are loaded from the root `.env` file in the project root directory. The following variables are required:

- `OPENAI_API_KEY`: API key for OpenAI (used for generating embeddings)
- `SUPABASE_PROJECT_URL`: URL for your Supabase project
- `SUPABASE_PRIVATE_API_KEY`: Private API key for your Supabase project

Note: The API does not create a separate `.env` file in the API directory. All environment variables are loaded from the root `.env` file. 
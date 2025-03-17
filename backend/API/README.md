# Employee Resume API

This API provides endpoints for querying and managing employee resume data stored in Pinecone.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file contains the following variables:

```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_REGION=your_pinecone_region
PINECONE_INDEX_NAME=your_pinecone_index_name
MISTRAL_API_KEY=your_mistral_api_key
```

## Running the API

Start the API server:

```bash
cd API
uvicorn main:app --reload
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

### 5. Add Employee

Add a new employee by uploading their resume PDF.

- **URL**: `/api/employees`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF file (required)
  - `employee_name`: Employee name (optional)

### 6. Delete Employee

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
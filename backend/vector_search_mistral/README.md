# PDF Search Engine

A powerful PDF search engine that uses Mistral OCR to extract text from PDFs, processes and chunks the text, generates dense and sparse embeddings, and indexes them in Pinecone for semantic and keyword search. Now with enhanced RAG capabilities using OpenAI.

## Features

- **OCR Text Extraction**: Uses Mistral AI's OCR capabilities to extract text from PDF files
- **Text Preprocessing**: Normalizes text and intelligently chunks it with overlap for better search context
- **Hybrid Vector Search**: Combines dense embeddings (semantic search) and sparse embeddings (keyword search) for better results
- **Scalable Storage**: Leverages Pinecone vector database for efficient storage and retrieval
- **Command-line Interface**: Easy-to-use CLI for processing PDFs and searching content
- **Enhanced RAG**: Uses OpenAI to summarize, analyze, explain, or provide detailed information based on search results
- **Person Queries**: Automatically detects queries about specific individuals and extracts their projects and roles

## Installation

### Automatic Setup (Recommended)

Use the provided setup script to automatically create a virtual environment and install dependencies:

```bash
# Make the setup script executable (if needed)
chmod +x backend/vector_search_mistral/setup.sh

# Run the setup script
./backend/vector_search_mistral/setup.sh
```

This script will:
1. Create a Python virtual environment in `backend/.venv` if it doesn't exist
2. Install all required dependencies
3. Make the `pdf-search` script executable
4. Create a `.env` file if it doesn't exist
5. Create necessary directories for PDF data

### Manual Installation

1. Create and activate a Python virtual environment:

```bash
# Create virtual environment in backend/.venv
python3 -m virtualenv backend/.venv

# Activate the virtual environment
source backend/.venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r backend/vector_search_mistral/requirements.txt
```

3. Set up environment variables in a `.env` file:

```
MISTRAL_API_KEY=your_mistral_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_REGION=your_pinecone_region
OPENAI_API_KEY=your_openai_api_key  # Only needed for RAG features
```

## Usage

### Activating the Virtual Environment

Before using the PDF search engine, make sure to activate the virtual environment:

```bash
source backend/.venv/bin/activate
```

### Using the pdf-search Script (Recommended)

The easiest way to use this system is with the provided pdf-search script:

```bash
# Process PDFs
./backend/vector_search_mistral/pdf-search process --pdf-dir pdf_data/raw-files

# Search PDFs
./backend/vector_search_mistral/pdf-search search "your search query"

# Search PDFs with RAG processing
./backend/vector_search_mistral/pdf-search search "your search query" --rag --rag-mode explain

# Find projects by a specific person
./backend/vector_search_mistral/pdf-search search "Give me all projects that John Smith has worked on" --rag
```

### Process and Index PDFs

Process all PDFs in a directory and index them in Pinecone:

```bash
./backend/vector_search_mistral/pdf-search process --pdf-dir pdf_data/raw-files
```

Options:
- `--pdf-dir`: Directory containing PDF files (default: 'pdf_data/raw-files')
- `--chunk-size`: Maximum size of text chunks in characters (default: 512)
- `--chunk-overlap`: Overlap between consecutive chunks in characters (default: 128)
- `--force`: Force reprocessing of all PDFs, even if already indexed

### Search PDFs

Search indexed PDF documents:

```bash
./backend/vector_search_mistral/pdf-search search "your search query"
```

Options:
- `--top-k`: Number of results to return (default: 5)
- `--alpha`: Weight for hybrid search (0 = sparse only, 1 = dense only) (default: 0.5)
- `--rag`: Enable RAG processing with OpenAI
- `--rag-mode`: RAG processing mode when --rag is enabled (choices: summarize, analyze, explain, detail, person) (default: summarize)
- `--model`: OpenAI model to use for RAG (default: gpt-3.5-turbo)

## RAG Processing Modes

When using the `--rag` flag, you can choose from different processing modes:

- **summarize**: Provides a concise summary of the search results (default)
- **analyze**: Analyzes the information and provides insights
- **explain**: Explains the concepts mentioned in the results
- **detail**: Provides detailed information based on the results
- **person**: Extracts information about a specific person, including projects they've worked on

The system automatically detects when you're asking about a specific person and switches to the person mode. For example:

```bash
# These queries will automatically use the person mode
./backend/vector_search_mistral/pdf-search search "Give me all projects that Manish Mardia has worked on" --rag
./backend/vector_search_mistral/pdf-search search "What projects has Jane Smith been involved in?" --rag
./backend/vector_search_mistral/pdf-search search "Show me John Doe's project history" --rag
```

Example:
```bash
# Get a detailed explanation of vector search concepts
./backend/vector_search_mistral/pdf-search search "vector search concepts" --rag --rag-mode explain

# Get projects for a specific person
./backend/vector_search_mistral/pdf-search search "Give me all projects that Manish Mardia has worked on" --rag
```

## Architecture

The system consists of several interconnected components:

1. **PDF Processor**: Extracts text from PDF files using Mistral OCR
2. **Text Preprocessor**: Normalizes and chunks the extracted text
3. **Embeddings Generator**: Creates dense (semantic) and sparse (keyword) embeddings for text chunks
4. **Pinecone Indexer**: Stores and retrieves embeddings from Pinecone
5. **Query Engine**: Provides a high-level API for searching documents
6. **OpenAI Processor**: Enhances search results with summarization, analysis, explanations, or detailed information

## Example

```python
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('/path/to/your/project'))

from backend.vector_search_mistral.main import process_and_index_pdfs, search_pdfs
from backend.vector_search_mistral.openai_processor import process_rag_results

# Process and index PDFs
stats = process_and_index_pdfs(pdf_dir="path/to/pdfs")

# Search for documents
results = search_pdfs("What is machine learning?")

# Apply RAG processing with OpenAI
rag_output = process_rag_results(
    query="What is machine learning?",
    search_results=results,
    mode="explain"
)

# Display the processed results
print(rag_output["processed_result"])

# Find projects for a specific person
person_query = "Give me all projects that Manish Mardia has worked on"
results = search_pdfs(person_query)
person_info = process_rag_results(
    query=person_query,
    search_results=results,
    mode="person"  # The system will also auto-detect this is a person query
)
print(person_info["processed_result"])
```

## Troubleshooting

### Virtual Environment Issues

If you encounter errors related to missing modules or dependencies, make sure you're using the correct virtual environment:

```bash
# Activate the virtual environment
source backend/.venv/bin/activate

# Verify the Python interpreter being used
which python

# Install any missing dependencies
pip install -r backend/vector_search_mistral/requirements.txt
```

### SSL Certificate Errors with NLTK

If you encounter SSL certificate verification errors when downloading NLTK data, the system will automatically attempt to bypass the certificate verification. If you still experience issues, you can manually download the required NLTK data:

```python
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt')
```

### Import Errors

If you encounter import errors, make sure your Python path includes the project root directory:

```python
import sys
import os
sys.path.insert(0, os.path.abspath('/path/to/your/project'))
```

### OpenAI API Issues

If you encounter errors with the OpenAI API, check:

1. Your API key is correctly set in the `.env` file
2. The OpenAI library is installed (`pip install openai>=1.0.0`)
3. You have sufficient credits in your OpenAI account
4. Your OpenAI API requests are not being rate limited

### Person Detection Issues

If the system doesn't automatically detect a person query:
1. Make sure you're using a clear query format like "Give me all projects that [Person Name] has worked on"
2. Explicitly specify the mode: `--rag-mode person`
3. Check that the person's name appears in the documents with the same spelling

## Performance Tuning

- **Chunk Size**: Smaller chunks (200-500 chars) work better for precise answers, larger chunks (1000-2000 chars) preserve more context
- **Alpha Parameter**: Adjust the alpha value to balance between semantic and keyword search
  - alpha=0.0: Use only keyword search (sparse vectors)
  - alpha=1.0: Use only semantic search (dense vectors)
  - alpha=0.5: Equal weight to both approaches (default)
- **RAG Mode**: Different modes are better for different use cases
  - summarize: Best for getting a quick overview
  - explain: Best for educational contexts
  - analyze: Best for finding insights
  - detail: Best for comprehensive information
  - person: Best for finding information about specific individuals and their projects

## Limitations

- Large PDF files may take longer to process with OCR
- Processing speed depends on Mistral API response time
- Maximum file size for Mistral OCR API may be limited (typically 50MB)
- NLTK download may fail due to SSL certificate issues (automatic fallback implemented)
- OpenAI API usage incurs costs based on token consumption
- Person detection may not work perfectly for uncommon names or ambiguous queries

## Future Improvements

- Add support for more document types (DOCX, TXT, etc.)
- Implement document summarization
- Add document similarity search
- Add document filtering by metadata
- Support for more LLMs beyond OpenAI
- Web interface for searching and viewing results
- Enhanced person and organization entity extraction
- Timeline visualization for person's project history 
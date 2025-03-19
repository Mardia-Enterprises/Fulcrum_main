# PDF Vector Search Engine

A production-ready PDF search engine that leverages AI technology to provide intelligent document searching capabilities. The system extracts text from PDFs, processes and chunks the content, generates semantic embeddings, and stores them in a vector database for efficient retrieval.

## Core Features

- **Advanced Text Extraction**: Extracts text content from PDF documents
- **Intelligent Text Processing**: Chunks text with contextual overlap for better search relevance
- **Vector Embeddings**: Generates dense semantic embeddings for understanding content meaning
- **Vector Database Storage**: Utilizes Supabase for efficient storage and retrieval of vectors
- **Hybrid Search**: Combines semantic and keyword search for comprehensive results
- **Enhanced RAG**: Integrates with OpenAI to provide summarization, explanation, and detailed analysis of search results
- **Person-Entity Intelligence**: Automatically detects and extracts information about specific individuals from documents

## System Architecture

The system consists of several interconnected components:

1. **PDF Processing Layer**: Extracts and normalizes text from PDF files
2. **Text Processing Layer**: Chunks and prepares text for embedding generation
3. **Embedding Layer**: Converts text into vector representations
4. **Storage Layer**: Manages vector storage and retrieval in Supabase
5. **Query Layer**: Handles search queries and retrieves relevant documents
6. **Enhancement Layer**: Applies OpenAI processing to search results for enhanced information retrieval

## Environment Setup

The system uses environment variables for configuration. These should be set in the root `.env` file (at the project root directory).

Required environment variables:
```
MISTRAL_API_KEY=your_mistral_api_key
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
OPENAI_API_KEY=your_openai_api_key  # Required for RAG features
```

Optional environment variables:
```
SUPABASE_TABLE_NAME=pdf_documents  # Default: "pdf_documents"
MISTRAL_MODEL=mistral-embed  # Default embedding model
OPENAI_MODEL=gpt-3.5-turbo  # Model for RAG features
```

Note: Do not create a separate .env file in the vector_search_mistral directory. Only use the root .env file.

## Production Installation

### Prerequisites

- Python 3.8+ 
- Supabase account (for vector database)
- Mistral AI API key (for embedding generation)
- OpenAI API key (for RAG features)

### Installation Steps

1. Install required packages:

```bash
cd backend
source .venv/bin/activate
pip install -r vector_search_mistral/requirements.txt
```

2. Set up environment variables:

```bash
# Required environment variables
export MISTRAL_API_KEY=your_mistral_api_key
export SUPABASE_PROJECT_URL=your_supabase_url
export SUPABASE_PRIVATE_API_KEY=your_supabase_private_key
export OPENAI_API_KEY=your_openai_api_key  # Only needed for RAG features

# Optional environment variables
export SUPABASE_TABLE_NAME=pdf_documents  # Defaults to "pdf_documents"
export MISTRAL_MODEL=mistral-embed     # Defaults to "mistral-embed"
export OPENAI_MODEL=gpt-3.5-turbo       # Defaults to "gpt-3.5-turbo"
```

3. Create necessary directories:

```bash
mkdir -p pdf_data/raw-files
```

4. Download NLTK data:

```bash
# Option 1: Simple download command
python -m nltk.downloader punkt

# Option 2: For SSL certificate issues
python -c "import nltk, ssl; ssl._create_default_https_context = ssl._create_unverified_context; nltk.download('punkt')"

# Option 3: Manual download
# Visit https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip
# Download and extract to ~/.nltk_data/tokenizers/punkt

# Option 4: Skip NLTK download completely
# The system has fallback methods for text processing when NLTK is unavailable
```

Note: The system uses the standard NLTK 'punkt' package, NOT 'punkt_tab'. The text processing will automatically fall back to simpler methods if NLTK is unavailable.

5. Set up Supabase vector storage:

- Log in to your Supabase project dashboard
- Navigate to the SQL Editor
- Copy the contents of `supabase_setup.sql` from this repository
- Run the SQL script to create the necessary tables and functions

The SQL script will:
- Enable the pgvector extension for vector similarity search
- Create a table named `pdf_documents` with the required schema
- Create indexes for efficient vector similarity search
- Set up SQL functions for searching and managing document vectors

## Production Usage

### Processing PDF Documents

```bash
cd backend
source .venv/bin/activate
python -m vector_search_mistral.run process --pdf-dir /path/to/pdf/files
```

Options:
- `--pdf-dir`: Directory containing PDF files to process (default: 'pdf_data/raw-files')
- `--chunk-size`: Maximum size of text chunks in characters (default: 512)
- `--chunk-overlap`: Overlap between consecutive chunks in characters (default: 128)
- `--force`: Force reprocessing of all PDFs, even if already indexed

### Searching PDF Documents

#### Basic Search

```bash
cd backend
source .venv/bin/activate
python -m vector_search_mistral.run search "your search query"
```

Options:
- `--top-k`: Number of results to return (default: 5)
- `--alpha`: Weight for hybrid search (0 = sparse only, 1 = dense only) (default: 0.5)

#### Enhanced Search with RAG

```bash
python -m vector_search_mistral.run search "your search query" --rag
```

### Special Query Types

#### Person Information Queries

The system automatically detects queries asking about specific individuals:

```bash
python -m vector_search_mistral.run search "What projects has John Smith worked on?" --rag
```

This will:
1. Detect that the query is about a person
2. Extract the person's name (John Smith)
3. Use specialized processing to find documents related to this person
4. Structure the response to include:
   - Basic profile information
   - Projects the person has worked on
   - Roles and responsibilities
   - Areas of expertise

### API Usage

You can also import and use the system within your Python code:

```python
from backend.vector_search_mistral.main import process_pdfs, search

# Process PDFs
result = process_pdfs(pdf_dir="/path/to/pdfs", chunk_size=500, chunk_overlap=50)
print(f"Processed {result['total_pdfs']} PDFs")

# Search
results = search("hydraulic systems design", top_k=5, use_rag=True)
print(f"Found {results['results_count']} results")
for result in results['rag_results']:
    print(result)
```

## Performance Optimization

For production environments with large document collections:

1. Adjust chunk sizes based on document types (smaller for dense technical documents)
2. Consider using batch processing for large collections
3. Implement caching for frequent queries
4. Scale Supabase resources according to collection size and query load

## Monitoring and Maintenance

- Regularly check your Supabase console for database performance
- Monitor API usage to stay within rate limits (Mistral AI, OpenAI)
- Consider implementing a document update strategy for evolving content

## Error Handling

The system includes robust error handling for:
- PDF processing failures
- API connectivity issues
- Database connection problems
- Query processing errors

Error logs are output to the console and can be redirected to a file for monitoring.

## Security Considerations

- API keys are stored in environment variables, not in code
- Vector storage in Supabase includes authentication
- Consider implementing access controls for sensitive documents

## Limitations

- Very large PDFs (100+ pages) may require custom processing strategies
- OCR capability depends on PDF quality (scanned documents may have reduced extraction quality)
- API rate limits apply to Mistral AI and OpenAI services

## Troubleshooting

### Common Issues

1. **Vector embedding failures**: Ensure your Mistral AI API key is valid
2. **Search returns no results**: Check if PDFs were properly processed and indexed
3. **Database connection errors**: Verify Supabase URL and API key
4. **PDF processing errors**: Ensure PDFs are not corrupted or password-protected

### Supabase Vector Storage Issues

If you're experiencing issues with storing vectors in Supabase:

1. **Vector dimension errors**: The system expects 1024-dimensional vectors from Mistral's embedding model. If you see errors about vector dimensions, it could be due to:
   - API errors returning empty vectors
   - Dimension mismatches between Mistral's output and Supabase's table schema

2. **Table creation errors**: The system will attempt to create the necessary table structure in Supabase. If this fails:
   - Check that your Supabase API key has SQL execution privileges
   - Manually run the following SQL in the Supabase SQL editor:

   ```sql
   -- Enable vector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   
   -- Create the table
   CREATE TABLE IF NOT EXISTS pdf_documents (
     id TEXT PRIMARY KEY,
     content TEXT,
     embedding VECTOR(1024),
     metadata JSONB,
     file_path TEXT,
     chunk_id TEXT,
     file_type TEXT
   );
   
   -- Create an index for efficient search
   CREATE INDEX IF NOT EXISTS pdf_documents_embedding_idx 
   ON pdf_documents 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   
   -- Create a function for similarity search
   CREATE OR REPLACE FUNCTION match_documents(
     query_embedding VECTOR(1024),
     match_threshold FLOAT,
     match_count INT
   )
   RETURNS TABLE (
     id TEXT,
     content TEXT,
     metadata JSONB,
     file_path TEXT,
     chunk_id TEXT,
     file_type TEXT,
     similarity FLOAT
   )
   LANGUAGE plpgsql
   AS $$
   BEGIN
     RETURN QUERY
     SELECT
       pdf_documents.id,
       pdf_documents.content,
       pdf_documents.metadata,
       pdf_documents.file_path,
       pdf_documents.chunk_id,
       pdf_documents.file_type,
       1 - (pdf_documents.embedding <=> query_embedding) AS similarity
     FROM pdf_documents
     WHERE 1 - (pdf_documents.embedding <=> query_embedding) > match_threshold
     ORDER BY similarity DESC
     LIMIT match_count;
   END;
   $$;
   ```

3. **Viewing stored vectors**: To check if vectors are stored properly, run this query in Supabase:
   ```sql
   SELECT id, content, array_length(embedding, 1) as dimensions 
   FROM pdf_documents 
   LIMIT 10;
   ```

### Handling Rate Limits

The system is designed to handle Mistral AI API rate limits gracefully:

1. **Partial Embedding Processing**: If rate limits are encountered during PDF processing, the system will:
   - Store all successfully generated embeddings in Supabase
   - Log detailed information about which chunks could not be processed
   - Provide clear feedback about the rate limit situation

2. **Recommended actions for rate limit errors**:
   - Wait 1-2 minutes before trying again (Mistral AI rate limits reset quickly)
   - Process smaller batches of PDFs at a time
   - Consider upgrading your Mistral AI plan for higher rate limits
   - Check your Mistral AI dashboard for current usage and limits

3. **Resuming after rate limits**: You can reprocess the same PDFs with the `--force` flag later:
   ```bash
   python -m vector_search_mistral.run process --pdf-dir pdf_data/raw-files --force
   ```
   Only chunks that weren't previously embedded will be processed.

## Future Improvements

- Multi-language support
- Image content extraction and indexing
- Automated document tagging
- Personalized search relevance 
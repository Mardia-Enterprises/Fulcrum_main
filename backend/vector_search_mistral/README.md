# PDF Vector Search Engine

A production-ready PDF search engine that leverages AI technology to provide intelligent document searching capabilities. The system extracts text from PDFs, processes and chunks the content, generates semantic embeddings, and stores them in a vector database for efficient retrieval.

## Core Features

- **Advanced Text Extraction**: Extracts text content from PDF documents
- **Intelligent Text Processing**: Chunks text with contextual overlap for better search relevance
- **Vector Embeddings**: Generates dense semantic embeddings for understanding content meaning
- **Vector Database Storage**: Utilizes Pinecone for efficient storage and retrieval of vectors
- **Hybrid Search**: Combines semantic and keyword search for comprehensive results
- **Enhanced RAG**: Integrates with OpenAI to provide summarization, explanation, and detailed analysis of search results
- **Person-Entity Intelligence**: Automatically detects and extracts information about specific individuals from documents

## System Architecture

The system consists of several interconnected components:

1. **PDF Processing Layer**: Extracts and normalizes text from PDF files
2. **Text Processing Layer**: Chunks and prepares text for embedding generation
3. **Embedding Layer**: Converts text into vector representations
4. **Storage Layer**: Manages vector storage and retrieval in Pinecone
5. **Query Layer**: Handles search queries and retrieves relevant documents
6. **Enhancement Layer**: Applies OpenAI processing to search results for enhanced information retrieval

## Production Installation

### Prerequisites

- Python 3.8+ 
- Pinecone account (for vector database)
- Mistral AI API key (for embedding generation)
- OpenAI API key (for RAG features)

### Installation Steps

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
# Required environment variables
export MISTRAL_API_KEY=your_mistral_api_key
export PINECONE_API_KEY=your_pinecone_api_key
export PINECONE_REGION=your_pinecone_region
export OPENAI_API_KEY=your_openai_api_key  # Only needed for RAG features

# Optional environment variables
export PINECONE_INDEX_NAME=your_index_name  # Defaults to "pdf-embeddings"
export PINECONE_NAMESPACE=your_namespace    # Defaults to "pdf-documents"
export MISTRAL_MODEL=your_mistral_model     # Defaults to "mistral-embed"
export OPENAI_MODEL=your_openai_model       # Defaults to "gpt-3.5-turbo"
```

3. Create necessary directories:

```bash
mkdir -p pdf_data/raw-files
```

4. Download NLTK data:

```bash
python -m nltk.downloader punkt
```

## Production Usage

### Processing PDF Documents

```bash
python run.py process --pdf-dir /path/to/pdf/files
```

Options:
- `--pdf-dir`: Directory containing PDF files to process (default: 'pdf_data/raw-files')
- `--chunk-size`: Maximum size of text chunks in characters (default: 512)
- `--chunk-overlap`: Overlap between consecutive chunks in characters (default: 128)
- `--force`: Force reprocessing of all PDFs, even if already indexed

### Searching PDF Documents

#### Basic Search

```bash
python run.py search "your search query"
```

Options:
- `--top-k`: Number of results to return (default: 5)
- `--alpha`: Weight for hybrid search (0 = sparse only, 1 = dense only) (default: 0.5)

#### Enhanced Search with RAG

```bash
python run.py search "your search query" --rag
```

Additional options for RAG:
- `--rag-mode`: Processing mode (summarize, analyze, explain, detail, person) (default: summarize)
- `--model`: OpenAI model to use (default: "gpt-3.5-turbo")
- `--no-raw`: Hide source documents in output

### Special Query Types

#### Person Information Queries

The system automatically detects queries about people and extracts relevant information:

```bash
python run.py search "What projects has Jane Smith worked on?" --rag
```

## API Usage

The system can be integrated into other applications using its Python API:

```python
from vector_search_mistral.main import process_and_index_pdfs, search_pdfs
from vector_search_mistral.openai_processor import process_rag_results

# Process PDFs
stats = process_and_index_pdfs(
    pdf_dir="/path/to/pdfs",
    chunk_size=512,
    chunk_overlap=128
)

# Search for documents
results = search_pdfs(
    query="What is machine learning?",
    top_k=5,
    alpha=0.5
)

# Enhance results with RAG processing
enhanced_results = process_rag_results(
    query="What is machine learning?",
    search_results=results,
    mode="explain"
)

# Access the processed content
print(enhanced_results["processed_result"])
```

## Performance Optimization

- **Chunk Size**: Adjust based on information density (200-500 chars for precise answers, 1000-2000 for context)
- **Search Alpha**: Tune to balance between semantic and keyword search (0.0-1.0)
- **RAG Modes**: Select appropriate mode based on information needs:
  - `summarize`: For concise overviews
  - `explain`: For educational information
  - `analyze`: For insights and patterns
  - `detail`: For comprehensive information
  - `person`: For extracting information about specific individuals

## Monitoring and Maintenance

Logs are generated during processing and search operations. Monitor these logs for any errors or performance issues.

Key metrics to track:
- Number of PDFs processed
- Number of chunks and embeddings generated
- Vector indexing performance
- Search response times
- OpenAI API usage

## Error Handling

The system includes robust error handling for common issues:
- PDF processing failures
- API connectivity issues
- Vector database connection problems
- Text chunking edge cases
- Missing NLTK resources

## Security Considerations

- API keys are stored as environment variables for security
- Sensitive data in PDFs should be properly secured
- Consider network security for API communications
- Implement appropriate access controls for the search system

## Limitations

- Maximum file size constraints may apply depending on available memory
- Processing very large PDFs may require additional resources
- API rate limits may affect throughput for Mistral and OpenAI services
- Enhanced RAG features incur OpenAI API costs based on token usage

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all required API keys are set in environment variables
2. **NLTK Data Download Failures**: Use the included workaround script or download manually
3. **Pinecone Connection Issues**: Verify region and API key settings
4. **PDF Extraction Problems**: Check PDF file format and encoding
5. **OpenAI API Issues**: Monitor rate limits and API credits

### Error Logging

Review logs for error messages. The system logs information about:
- PDF processing status
- Text chunking outcomes
- Embedding generation
- Vector indexing
- Search operations
- RAG processing

## License

This software is proprietary and confidential. 
# PDF Search Engine

A powerful PDF search engine that uses Mistral OCR to extract text from PDFs, processes and chunks the text, generates dense and sparse embeddings, and indexes them in Pinecone for semantic and keyword search.

## Features

- **OCR Text Extraction**: Uses Mistral AI's OCR capabilities to extract text from PDF files
- **Text Preprocessing**: Normalizes text and intelligently chunks it with overlap for better search context
- **Hybrid Vector Search**: Combines dense embeddings (semantic search) and sparse embeddings (keyword search) for better results
- **Scalable Storage**: Leverages Pinecone vector database for efficient storage and retrieval
- **Command-line Interface**: Easy-to-use CLI for processing PDFs and searching content

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:

```
MISTRAL_API_KEY=your_mistral_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_REGION=your_pinecone_region
```

## Usage

### Process and Index PDFs

Process all PDFs in a directory and index them in Pinecone:

```bash
python -m main process --pdf-dir pdf_data/raw-files
```

Options:
- `--pdf-dir`: Directory containing PDF files (default: 'pdf_data/raw-files')
- `--chunk-size`: Maximum size of text chunks in characters (default: 512)
- `--chunk-overlap`: Overlap between consecutive chunks in characters (default: 128)
- `--force`: Force reprocessing of all PDFs, even if already indexed

### Search PDFs

Search indexed PDF documents:

```bash
python -m main search "your search query"
```

Options:
- `--top-k`: Number of results to return (default: 5)
- `--alpha`: Weight for hybrid search (0 = sparse only, 1 = dense only) (default: 0.5)

## Architecture

The system consists of several interconnected components:

1. **PDF Processor**: Extracts text from PDF files using Mistral OCR
2. **Text Preprocessor**: Normalizes and chunks the extracted text
3. **Embeddings Generator**: Creates dense (semantic) and sparse (keyword) embeddings for text chunks
4. **Pinecone Indexer**: Stores and retrieves embeddings from Pinecone
5. **Query Engine**: Provides a high-level API for searching documents

## Example

```python
from vector_search_mistral import process_and_index_pdfs, search_pdfs

# Process and index PDFs
stats = process_and_index_pdfs(pdf_dir="path/to/pdfs")

# Search for documents
results = search_pdfs("What is machine learning?")

# Display results
for result in results:
    print(f"Document: {result['filename']}")
    print(f"Score: {result['score']}")
    for match in result['text_matches']:
        print(f"- {match['text'][:100]}...")
```

## Performance Tuning

- **Chunk Size**: Smaller chunks (200-500 chars) work better for precise answers, larger chunks (1000-2000 chars) preserve more context
- **Alpha Parameter**: Adjust the alpha value to balance between semantic and keyword search
  - alpha=0.0: Use only keyword search (sparse vectors)
  - alpha=1.0: Use only semantic search (dense vectors)
  - alpha=0.5: Equal weight to both approaches (default)

## Limitations

- Large PDF files may take longer to process with OCR
- Processing speed depends on Mistral API response time
- Maximum file size for Mistral OCR API may be limited

## Future Improvements

- Add support for more document types (DOCX, TXT, etc.)
- Implement document summarization
- Add document similarity search
- Add document filtering by metadata 
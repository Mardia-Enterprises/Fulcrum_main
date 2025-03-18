"""
PDF Search Engine based on Mistral OCR and Pinecone vector database.
"""

import os
import sys

# Add the parent directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Try to import the modules, but don't fail if they're not available yet
try:
    from backend.vector_search_mistral.pdf_processor import MistralPDFProcessor
    from backend.vector_search_mistral.text_preprocessor import TextPreprocessor
    from backend.vector_search_mistral.embeddings_generator import EmbeddingsGenerator
    from backend.vector_search_mistral.pinecone_indexer import PineconeIndexer
    from backend.vector_search_mistral.query_engine import QueryEngine
    from backend.vector_search_mistral.main import process_and_index_pdfs, search_pdfs

    __all__ = [
        'MistralPDFProcessor',
        'TextPreprocessor',
        'EmbeddingsGenerator',
        'PineconeIndexer',
        'QueryEngine',
        'process_and_index_pdfs',
        'search_pdfs'
    ]
except ImportError:
    # Don't fail if modules can't be imported during initial package setup
    pass 
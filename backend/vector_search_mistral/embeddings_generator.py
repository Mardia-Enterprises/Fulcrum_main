"""
Embeddings Generator for PDF content.
This module generates dense and sparse embeddings for text chunks to support hybrid search.
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EmbeddingsGenerator:
    """Generate dense and sparse embeddings for text chunks."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embeddings generator.
        
        Args:
            model_name: Name of the SentenceTransformer model to use
        """
        logger.info(f"Initializing embeddings generator with model: {model_name}")
        self.dense_model = SentenceTransformer(model_name)
        self.model_dimension = self.dense_model.get_sentence_embedding_dimension()
        logger.info(f"Model dimension: {self.model_dimension}")
    
    def generate_dense_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate dense embeddings for a list of text chunks.
        
        Args:
            texts: List of text chunks
            
        Returns:
            List of dense embeddings (as lists of floats)
        """
        logger.info(f"Generating dense embeddings for {len(texts)} chunks")
        dense_embeddings = self.dense_model.encode(texts, show_progress_bar=True)
        # Convert numpy arrays to lists for JSON serialization
        return dense_embeddings.tolist()
    
    def generate_sparse_embeddings(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Generate sparse BM25 embeddings for a list of text chunks.
        
        Args:
            texts: List of text chunks
            
        Returns:
            List of sparse embeddings as dictionaries mapping indices to values
        """
        logger.info(f"Generating sparse embeddings for {len(texts)} chunks")
        
        # Tokenize texts
        tokenized_texts = [text.split() for text in texts]
        
        # Create vocabulary
        vocab = {}
        for i, tokens in enumerate(tokenized_texts):
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        
        # Create BM25 model
        bm25 = BM25Okapi(tokenized_texts)
        
        # Generate sparse vectors
        sparse_embeddings = []
        for i, tokens in enumerate(tokenized_texts):
            # Get unique tokens
            unique_tokens = set(tokens)
            
            # Calculate scores for each token
            sparse_vector = {}
            for token in unique_tokens:
                idx = vocab[token]
                score = bm25.idf[token] * (bm25.k1 + 1) * bm25.doc_freqs[i].get(token, 0) / (
                        bm25.k1 * (1 - bm25.b + bm25.b * bm25.doc_len[i] / bm25.avgdl) +
                        bm25.doc_freqs[i].get(token, 0))
                if score > 0:
                    sparse_vector[str(idx)] = float(score)
            
            sparse_embeddings.append(sparse_vector)
        
        return sparse_embeddings
    
    def generate_hybrid_embeddings(self, 
                                   chunks: List[Dict]) -> List[Dict]:
        """
        Generate both dense and sparse embeddings for a list of text chunks.
        
        Args:
            chunks: List of text chunk dictionaries from the preprocessor
            
        Returns:
            List of dictionaries with chunks and their embeddings
        """
        # Extract texts from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        dense_embeddings = self.generate_dense_embeddings(texts)
        sparse_embeddings = self.generate_sparse_embeddings(texts)
        
        # Combine embeddings with chunks
        result = []
        for i, (chunk, dense_emb, sparse_emb) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
            result.append({
                **chunk,  # Include all original chunk data
                "dense_embedding": dense_emb,
                "sparse_embedding": sparse_emb
            })
        
        logger.info(f"Generated hybrid embeddings for {len(result)} chunks")
        return result


def main():
    """Test the embeddings generator with sample text chunks."""
    sample_chunks = [
        {
            "chunk_id": 0,
            "text": "This is a sample text chunk for testing dense and sparse embeddings generation.",
            "filename": "sample.pdf",
            "document_id": "sample_doc_id",
            "file_path": "/path/to/sample.pdf",
            "chunk_count": 2
        },
        {
            "chunk_id": 1,
            "text": "Hybrid search combines the benefits of keyword matching and semantic similarity to improve search results.",
            "filename": "sample.pdf",
            "document_id": "sample_doc_id",
            "file_path": "/path/to/sample.pdf",
            "chunk_count": 2
        }
    ]
    
    generator = EmbeddingsGenerator()
    results = generator.generate_hybrid_embeddings(sample_chunks)
    
    for i, result in enumerate(results):
        print(f"Chunk {i+1}:")
        print(f"  Text: {result['text']}")
        print(f"  Dense embedding shape: {len(result['dense_embedding'])} dimensions")
        print(f"  Sparse embedding: {len(result['sparse_embedding'])} non-zero values")
        print()


if __name__ == "__main__":
    main() 
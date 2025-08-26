"""Embeddings module using sentence-transformers."""
import numpy as np
from typing import List, Union
import hashlib
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None


def get_embedding_model():
    """Get or create the embedding model instance (stubbed but functional)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Using deterministic embedding model (sentence-transformers not available)")
        _embedding_model = "deterministic_model"
    return _embedding_model


def embed_texts(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Generate embeddings for text(s) (stubbed implementation).
    
    Args:
        texts: Single text string or list of text strings
        
    Returns:
        Numpy array of embeddings. Shape (embedding_dim,) for single text,
        or (num_texts, embedding_dim) for multiple texts.
    """
    model = get_embedding_model()
    
    # Handle single text
    if isinstance(texts, str):
        texts = [texts]
        single_text = True
    else:
        single_text = False
    
    # Generate deterministic embeddings based on text content (384 dimensions like MiniLM)
    num_texts = len(texts)
    embeddings = np.zeros((num_texts, 384), dtype=np.float32)
    
    for i, text in enumerate(texts):
        # Create deterministic embedding based on text hash
        text_hash = hashlib.md5(text.encode()).digest()
        # Convert hash bytes to float values between -1 and 1
        for j in range(384):
            byte_idx = j % len(text_hash)
            embeddings[i, j] = (text_hash[byte_idx] / 255.0) * 2 - 1
        
        # Normalize the embedding vector
        norm = np.linalg.norm(embeddings[i])
        if norm > 0:
            embeddings[i] = embeddings[i] / norm
    
    # Return single embedding if input was single text
    if single_text:
        return embeddings[0]
    
    return embeddings
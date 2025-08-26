"""Embeddings module using sentence-transformers."""
import numpy as np
from typing import List, Union
# from sentence_transformers import SentenceTransformer
# Temporarily disabled due to compatibility issues with Python 3.13
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None


def get_embedding_model():
    """Get or create the embedding model instance (stubbed)."""
    global _embedding_model
    if _embedding_model is None:
        logger.warning("Embedding model stubbed - sentence-transformers not available")
        _embedding_model = "stubbed_model"
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
    
    # Generate dummy embeddings (384 dimensions like MiniLM)
    num_texts = len(texts)
    embeddings = np.random.rand(num_texts, 384).astype(np.float32)
    
    # Return single embedding if input was single text
    if single_text:
        return embeddings[0]
    
    return embeddings
"""Embeddings module using sentence-transformers."""
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create the embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def embed_texts(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Generate embeddings for text(s) using sentence-transformers.
    
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
    
    # Generate embeddings
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    # Return single embedding if input was single text
    if single_text:
        return embeddings[0]
    
    return embeddings
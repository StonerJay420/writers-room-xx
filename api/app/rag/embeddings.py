"""Embeddings module with improved text embeddings."""
import numpy as np
from typing import List, Union, Optional
import hashlib
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_embedding_model = None

# Try to import sentence-transformers, fall back to improved deterministic model
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers available")
except ImportError:
    SentenceTransformer = None  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not available, using improved deterministic model")


class ImprovedDeterministicEmbedder:
    """Improved deterministic embedding model with better semantic representation."""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.vocabulary = {}
        self.vocab_size = 10000  # Common words vocabulary
        
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into tokens."""
        # Lowercase and remove special characters
        text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = text.split()
        return tokens
    
    def _get_word_embedding(self, word: str) -> np.ndarray:
        """Generate consistent embedding for a word."""
        # Use hash to generate consistent embedding
        word_hash = hashlib.sha256(word.encode()).digest()
        embedding = np.array([
            (word_hash[i % len(word_hash)] / 255.0) * 2 - 1 
            for i in range(self.embedding_dim)
        ], dtype=np.float32)
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode texts to embeddings."""
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
            
        embeddings = []
        
        for text in texts:
            tokens = self._preprocess_text(text)
            
            if not tokens:
                # Empty text
                embedding = np.zeros(self.embedding_dim, dtype=np.float32)
            else:
                # Average word embeddings
                word_embeddings = [self._get_word_embedding(token) for token in tokens]
                embedding = np.mean(word_embeddings, axis=0).astype(np.float32)
                
                # Normalize final embedding
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
            
            embeddings.append(embedding)
        
        embeddings_array = np.array(embeddings)
        
        if single_input:
            return embeddings_array[0]
        return embeddings_array


def get_embedding_model():
    """Get or create the embedding model instance."""
    global _embedding_model
    if _embedding_model is None:
        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
            try:
                # Use a lightweight model
                _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers model: {e}")
                _embedding_model = ImprovedDeterministicEmbedder()
                logger.info("Using improved deterministic embedder")
        else:
            _embedding_model = ImprovedDeterministicEmbedder()
            logger.info("Using improved deterministic embedder")
    return _embedding_model


def embed_texts(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Generate embeddings for text(s).
    
    Args:
        texts: Single text string or list of text strings
        
    Returns:
        Numpy array of embeddings. Shape (embedding_dim,) for single text,
        or (num_texts, embedding_dim) for multiple texts.
    """
    model = get_embedding_model()
    
    try:
        # Use the model's encode method
        embeddings = model.encode(texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Fallback to simple deterministic method
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        embeddings = np.zeros((len(texts), 384), dtype=np.float32)
        
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).digest()
            for j in range(384):
                byte_idx = j % len(text_hash)
                embeddings[i, j] = (text_hash[byte_idx] / 255.0) * 2 - 1
            
            norm = np.linalg.norm(embeddings[i])
            if norm > 0:
                embeddings[i] = embeddings[i] / norm
        
        if single_text:
            return embeddings[0]
        return embeddings


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    # Ensure embeddings are normalized
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # Cosine similarity
    similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
    return float(similarity)


def batch_embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for texts in batches for memory efficiency.
    
    Args:
        texts: List of text strings
        batch_size: Size of each batch
        
    Returns:
        Numpy array of embeddings
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, 384)
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = embed_texts(batch)
        
        # Ensure 2D array
        if len(batch_embeddings.shape) == 1:
            batch_embeddings = batch_embeddings.reshape(1, -1)
        
        all_embeddings.append(batch_embeddings)
    
    return np.vstack(all_embeddings)
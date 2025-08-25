"""RAG (Retrieval-Augmented Generation) module for Writers Room X."""

from .embeddings import embed_texts, get_embedding_model
from .chunker import chunk_markdown, chunk_text
from .chroma_client import ChromaClient, get_chroma_client
from .retrieve import retrieve_canon, retrieve_similar

__all__ = [
    "embed_texts",
    "get_embedding_model",
    "chunk_markdown",
    "chunk_text",
    "ChromaClient",
    "get_chroma_client",
    "retrieve_canon",
    "retrieve_similar",
]
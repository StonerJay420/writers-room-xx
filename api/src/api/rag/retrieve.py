"""Retrieval functions for RAG."""
from typing import List, Dict, Any, Optional
from .chroma_client import get_chroma_client
from .embeddings import embed_texts
import logging

logger = logging.getLogger(__name__)


def retrieve_canon(
    query: str,
    k: int = 12,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve canon information with source receipts.
    
    Args:
        query: Query text
        k: Number of results to retrieve
        filters: Optional metadata filters
        
    Returns:
        List of retrieved passages with metadata including:
        - text: The passage text
        - source_path: Path to source file
        - start_line: Starting line number
        - end_line: Ending line number
    """
    client = get_chroma_client()
    
    # Search in both codex and manuscript collections
    all_results = []
    
    for collection in ["codex_docs", "manuscript_scenes"]:
        results = client.query(
            collection=collection,
            query_text=query,
            top_k=k // 2,  # Split k between collections
            filters=filters
        )
        
        # Format results with receipts
        for i, doc_id in enumerate(results.get("ids", [])):
            metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
            document = results["documents"][i] if i < len(results.get("documents", [])) else ""
            
            all_results.append({
                "text": document or metadata.get("text", ""),
                "source_path": metadata.get("source_path", "unknown"),
                "start_line": metadata.get("start_line", 0),
                "end_line": metadata.get("end_line", 0),
                "distance": results["distances"][i] if i < len(results["distances"]) else 1.0,
                "collection": collection
            })
    
    # Sort by distance and return top k
    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results[:k]


def retrieve_similar(
    text: str,
    collection: str = "manuscript_scenes",
    k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve similar passages from a specific collection.
    
    Args:
        text: Text to find similar passages for
        collection: Collection to search in
        k: Number of results
        filters: Optional metadata filters
        
    Returns:
        List of similar passages with metadata
    """
    client = get_chroma_client()
    
    # Generate embedding for the text
    embedding = embed_texts(text)
    
    # Query collection
    results = client.query(
        collection=collection,
        query_embedding=embedding,
        top_k=k,
        filters=filters
    )
    
    # Format results
    formatted_results = []
    for i, doc_id in enumerate(results.get("ids", [])):
        metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
        document = results["documents"][i] if i < len(results.get("documents", [])) else ""
        
        formatted_results.append({
            "id": doc_id,
            "text": document or metadata.get("text", ""),
            "metadata": metadata,
            "similarity": 1.0 - results["distances"][i] if i < len(results["distances"]) else 0.0
        })
    
    return formatted_results
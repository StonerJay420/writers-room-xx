"""ChromaDB client wrapper for vector storage."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Union
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ChromaClient:
    """Wrapper for ChromaDB operations."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client with persistence."""
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB client initialized with persist_directory: {persist_directory}")
    
    def upsert(
        self,
        collection: str,
        embeddings: Union[np.ndarray, List[List[float]]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Upsert embeddings and metadata to a collection.
        
        Args:
            collection: Name of the collection
            embeddings: Numpy array of embeddings
            metadatas: List of metadata dictionaries
            ids: List of unique IDs
        """
        # Get or create collection
        coll = self.client.get_or_create_collection(name=collection)
        
        # Convert embeddings to list format if needed
        if isinstance(embeddings, np.ndarray):
            if len(embeddings.shape) == 1:
                embeddings_list = [embeddings.tolist()]
            else:
                embeddings_list = embeddings.tolist()
        else:
            embeddings_list = embeddings
        
        # Upsert to collection
        coll.upsert(
            embeddings=embeddings_list,  # type: ignore
            metadatas=metadatas,  # type: ignore
            ids=ids
        )
        
        logger.info(f"Upserted {len(ids)} items to collection '{collection}'")
    
    def query(
        self,
        collection: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[np.ndarray] = None,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a collection for similar vectors.
        
        Args:
            collection: Name of the collection
            query_text: Text to search for (will be embedded)
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Query results with ids, distances, metadatas
        """
        try:
            coll = self.client.get_collection(name=collection)
        except Exception as e:
            logger.warning(f"Collection '{collection}' not found: {e}")
            return {"ids": [], "distances": [], "metadatas": []}
        
        # Execute query based on input type
        if query_embedding is not None:
            if isinstance(query_embedding, np.ndarray):
                query_embedding_list = query_embedding.tolist()
            else:
                query_embedding_list = query_embedding
            results = coll.query(
                query_embeddings=[query_embedding_list],
                n_results=top_k,
                where=filters
            )
        elif query_text is not None:
            results = coll.query(
                query_texts=[query_text],
                n_results=top_k,
                where=filters
            )
        else:
            raise ValueError("Either query_text or query_embedding must be provided")
        
        # Flatten results since we always query with single embedding/text
        ids_list = results.get("ids") or [[]]
        distances_list = results.get("distances") or [[]]
        metadatas_list = results.get("metadatas") or [[]]
        documents_list = results.get("documents") or [[]]
        
        return {
            "ids": ids_list[0] if len(ids_list) > 0 else [],
            "distances": distances_list[0] if len(distances_list) > 0 else [],
            "metadatas": metadatas_list[0] if len(metadatas_list) > 0 else [],
            "documents": documents_list[0] if len(documents_list) > 0 else []
        }
    
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection)
            logger.info(f"Deleted collection '{collection}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection}': {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        collections = self.client.list_collections()
        return [c.name for c in collections]


# Global client instance
_chroma_client = None


def get_chroma_client(persist_directory: str = "./chroma_db") -> ChromaClient:
    """Get or create ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient(persist_directory)
    return _chroma_client
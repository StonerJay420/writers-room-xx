"""Semantic search service for manuscript and codex content."""
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from ..models import SceneEmbedding, Scene
from ..db import get_read_session


class SearchService:
    """Service for semantic and keyword search across content."""
    
    def __init__(self):
        self.embedding_dim = 384
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query (stub for now)."""
        # This is a placeholder - in production you'd use a real embedding model
        # For now, generate a deterministic fake embedding
        import hashlib
        
        query_hash = hashlib.md5(query.encode()).hexdigest()
        embedding = []
        
        for i in range(0, min(len(query_hash), self.embedding_dim * 2), 2):
            if i < len(query_hash) - 1:
                hex_val = query_hash[i:i+2]
                val = (int(hex_val, 16) - 128) / 128.0
                embedding.append(val)
        
        # Pad or truncate to correct dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        return embedding[:self.embedding_dim]
    
    def semantic_search(
        self,
        query: str,
        db: Session,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity."""
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Get all embeddings from database
        embeddings = db.query(SceneEmbedding).all()
        
        # Calculate similarities
        results = []
        for embedding in embeddings:
            # Parse embedding (stored as JSON in SQLite)
            if isinstance(embedding.embedding, str):
                vec = json.loads(embedding.embedding)
            else:
                vec = embedding.embedding
            
            similarity = self.cosine_similarity(query_embedding, vec)
            
            if similarity >= threshold:
                results.append({
                    'scene_id': embedding.scene_id,
                    'chunk_no': embedding.chunk_no,
                    'content': embedding.content[:200] + '...' if len(embedding.content) > 200 else embedding.content,
                    'similarity': similarity
                })
        
        # Sort by similarity and limit
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def keyword_search(
        self,
        query: str,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform keyword search in scene content."""
        
        # Search in scene embeddings content
        query_lower = f"%{query.lower()}%"
        
        embeddings = db.query(SceneEmbedding).filter(
            SceneEmbedding.content.ilike(query_lower)
        ).limit(limit).all()
        
        results = []
        for embedding in embeddings:
            # Find the position of the query in content
            content_lower = embedding.content.lower()
            pos = content_lower.find(query.lower())
            
            # Extract context around the match
            start = max(0, pos - 50)
            end = min(len(embedding.content), pos + len(query) + 50)
            snippet = embedding.content[start:end]
            
            if start > 0:
                snippet = "..." + snippet
            if end < len(embedding.content):
                snippet = snippet + "..."
            
            results.append({
                'scene_id': embedding.scene_id,
                'chunk_no': embedding.chunk_no,
                'snippet': snippet,
                'match_type': 'keyword'
            })
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        db: Session,
        limit: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword search results."""
        
        # Get semantic results
        semantic_results = self.semantic_search(query, db, limit * 2)
        
        # Get keyword results
        keyword_results = self.keyword_search(query, db, limit * 2)
        
        # Combine and deduplicate
        combined = {}
        
        # Add semantic results with weighted scores
        for result in semantic_results:
            key = f"{result['scene_id']}_{result['chunk_no']}"
            combined[key] = {
                **result,
                'score': result['similarity'] * semantic_weight,
                'type': 'semantic'
            }
        
        # Add or update with keyword results
        keyword_weight = 1 - semantic_weight
        for result in keyword_results:
            key = f"{result['scene_id']}_{result['chunk_no']}"
            if key in combined:
                combined[key]['score'] += keyword_weight
                combined[key]['type'] = 'hybrid'
            else:
                combined[key] = {
                    **result,
                    'score': keyword_weight,
                    'type': 'keyword'
                }
        
        # Sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:limit]


# Global search service instance
search_service = SearchService()
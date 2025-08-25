"""Search router for semantic and keyword search."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db import get_read_session
from ..services.search_service import search_service


router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    search_type: str = "hybrid"  # semantic, keyword, hybrid
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Search result model."""
    scene_id: str
    chunk_no: int
    content: str
    score: float
    match_type: str


@router.post("/query", response_model=List[SearchResult])
async def search_content(
    request: SearchRequest,
    db: Session = Depends(get_read_session)
):
    """Perform search across manuscript and codex content."""
    
    try:
        if request.search_type == "semantic":
            results = search_service.semantic_search(
                request.query,
                db,
                request.limit
            )
        elif request.search_type == "keyword":
            results = search_service.keyword_search(
                request.query,
                db,
                request.limit
            )
        else:  # hybrid
            results = search_service.hybrid_search(
                request.query,
                db,
                request.limit
            )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(SearchResult(
                scene_id=result.get('scene_id', ''),
                chunk_no=result.get('chunk_no', 0),
                content=result.get('content', result.get('snippet', '')),
                score=result.get('score', result.get('similarity', 0.0)),
                match_type=result.get('type', result.get('match_type', 'unknown'))
            ))
        
        return formatted_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
    prefix: str = Query(..., min_length=2),
    limit: int = Query(default=5, le=20),
    db: Session = Depends(get_read_session)
):
    """Get search suggestions based on prefix."""
    
    # For now, return simple keyword matches
    # In production, you'd implement proper autocomplete
    
    suggestions = []
    
    # Get unique words from content that start with prefix
    from ..models import SceneEmbedding
    
    embeddings = db.query(SceneEmbedding).limit(100).all()
    
    word_set = set()
    for embedding in embeddings:
        words = embedding.content.split()
        for word in words:
            cleaned = word.lower().strip('.,!?;:"')
            if cleaned.startswith(prefix.lower()):
                word_set.add(cleaned)
    
    suggestions = list(word_set)[:limit]
    
    return {"suggestions": suggestions}
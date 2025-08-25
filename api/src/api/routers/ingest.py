"""Ingestion router for indexing documents."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from ..db import get_read_session, get_write_session
from ..ingest.indexer import index_files


router = APIRouter(prefix="/ingest", tags=["ingest"])


class IndexRequest(BaseModel):
    """Request model for indexing documents."""
    paths: List[str]
    reindex: bool = False


class IndexResponse(BaseModel):
    """Response model for indexing results."""
    indexed_docs: int
    scenes: int
    chunks: int
    errors: int


@router.post("/index", response_model=IndexResponse)
async def index_documents(
    request: IndexRequest,
    db: Session = Depends(get_write_session)
):
    """Index documents from the specified paths."""
    try:
        results = index_files(request.paths, request.reindex)
        return IndexResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""Scene management router."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from pathlib import Path

from ..db import get_read_session
from ..models import Scene


router = APIRouter(prefix="/scenes", tags=["scenes"])


class SceneMetadata(BaseModel):
    """Scene metadata response model."""
    id: str
    chapter: int
    order_in_chapter: int
    pov: Optional[str]
    location: Optional[str]
    beats_json: Optional[Dict[str, Any]]
    links_json: Optional[Dict[str, Any]]


class SceneDetail(BaseModel):
    """Scene detail response model."""
    meta: SceneMetadata
    text: str


@router.get("", response_model=List[SceneMetadata])
async def list_scenes(
    chapter: Optional[int] = Query(None, description="Filter by chapter"),
    search: Optional[str] = Query(None, description="Search in scene text"),
    db: Session = Depends(get_read_session)
):
    """List all scenes with optional filtering."""
    query = db.query(Scene)
    
    # Apply filters
    if chapter is not None:
        query = query.filter(Scene.chapter == chapter)
    
    if search:
        # For now, just check if the search term is in the path
        # In a real implementation, this would search the actual text content
        query = query.filter(Scene.text_path.contains(search))
    
    # Order by chapter and scene number
    query = query.order_by(Scene.chapter, Scene.order_in_chapter)
    
    scenes = query.all()
    
    return [
        SceneMetadata(
            id=scene.id,
            chapter=scene.chapter,
            order_in_chapter=scene.order_in_chapter,
            pov=scene.pov,
            location=scene.location,
            beats_json=scene.beats_json,
            links_json=scene.links_json
        )
        for scene in scenes
    ]


@router.get("/{scene_id}", response_model=SceneDetail)
async def get_scene(
    scene_id: str,
    db: Session = Depends(get_read_session)
):
    """Get a specific scene by ID."""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found")
    
    # Read the actual text content from the file
    text = ""
    if scene.text_path:
        text_path = Path(scene.text_path)
        if text_path.exists():
            content = text_path.read_text(encoding='utf-8')
            
            # Remove front matter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    text = parts[2].strip()
                else:
                    text = content
            else:
                text = content
        else:
            text = f"[Text file not found: {scene.text_path}]"
    
    return SceneDetail(
        meta=SceneMetadata(
            id=scene.id,
            chapter=scene.chapter,
            order_in_chapter=scene.order_in_chapter,
            pov=scene.pov,
            location=scene.location,
            beats_json=scene.beats_json,
            links_json=scene.links_json
        ),
        text=text
    )
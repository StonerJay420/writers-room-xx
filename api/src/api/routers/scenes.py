
"""Scene management router."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/scenes", tags=["scenes"])


class SceneMetadata(BaseModel):
    """Scene metadata response model."""
    id: str
    chapter: int
    order_in_chapter: int
    pov: Optional[str] = None
    location: Optional[str] = None
    beats_json: Optional[Dict[str, Any]] = None
    links_json: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[SceneMetadata])
async def list_scenes(
    chapter: Optional[int] = Query(None, description="Filter by chapter"),
    search: Optional[str] = Query(None, description="Search in scene text")
):
    """List all scenes with optional filtering."""
    scenes = []
    
    # Read from data/manuscript directory
    manuscript_dir = Path("data/manuscript")
    if manuscript_dir.exists():
        for md_file in manuscript_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            scene_id = md_file.stem
            
            # Extract chapter and scene from filename pattern like "ch01_s02"
            import re
            match = re.match(r'ch(\d+)_s(\d+)', scene_id)
            if match:
                chapter_num = int(match.group(1))
                order_num = int(match.group(2))
            else:
                chapter_num = 1
                order_num = 1
            
            # Apply chapter filter if specified
            if chapter is not None and chapter_num != chapter:
                continue
                
            # Apply search filter if specified  
            if search and search.lower() not in scene_id.lower():
                continue
                
            scenes.append(SceneMetadata(
                id=scene_id,
                chapter=chapter_num,
                order_in_chapter=order_num,
                pov=None,
                location=None,
                beats_json={},
                links_json={}
            ))
    
    # Sort by chapter and order
    scenes.sort(key=lambda s: (s.chapter, s.order_in_chapter))
    
    return scenes


@router.get("/{scene_id}")
async def get_scene(scene_id: str):
    """Get a specific scene by ID."""
    scene_path = Path(f"data/manuscript/{scene_id}.md")
    
    if not scene_path.exists():
        raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found")
    
    content = scene_path.read_text(encoding='utf-8')
    
    # Remove frontmatter if present
    text = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            text = parts[2].strip()
    
    return {
        "id": scene_id,
        "text": text,
        "path": str(scene_path)
    }

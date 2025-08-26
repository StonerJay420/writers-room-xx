
"""Scene management router."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pathlib import Path
import yaml
import re

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


class CreateSceneRequest(BaseModel):
    """Request model for creating a new scene."""
    chapter: int
    order_in_chapter: int
    title: Optional[str] = None
    pov: Optional[str] = None
    location: Optional[str] = None
    beats: Optional[List[str]] = None
    content: str = ""
    links: Optional[Dict[str, Any]] = None


class CreateSceneResponse(BaseModel):
    """Response model for scene creation."""
    id: str
    chapter: int
    order_in_chapter: int
    path: str
    status: str


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


@router.post("", response_model=CreateSceneResponse)
async def create_scene(request: CreateSceneRequest):
    """Create a new scene with the specified metadata and content."""
    # Generate scene ID
    scene_id = f"ch{request.chapter:02d}_s{request.order_in_chapter:02d}"
    
    # Create data/manuscript directory if it doesn't exist
    manuscript_dir = Path("data/manuscript")
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if scene already exists
    scene_path = manuscript_dir / f"{scene_id}.md"
    if scene_path.exists():
        raise HTTPException(status_code=409, detail=f"Scene {scene_id} already exists")
    
    # Prepare frontmatter
    frontmatter: Dict[str, Any] = {
        "chapter": request.chapter,
        "scene": request.order_in_chapter,
    }
    
    if request.pov:
        frontmatter["pov"] = request.pov
    if request.location:
        frontmatter["location"] = request.location
    if request.beats:
        frontmatter["beats"] = request.beats
    if request.links:
        frontmatter["links"] = request.links
    
    # Create markdown content with YAML frontmatter
    content_lines = ["---"]
    content_lines.append(yaml.dump(frontmatter, default_flow_style=False).strip())
    content_lines.append("---")
    
    if request.title:
        content_lines.append(f"\n# {request.title}\n")
    
    content_lines.append(request.content)
    
    full_content = "\n".join(content_lines)
    
    # Write the file
    scene_path.write_text(full_content, encoding='utf-8')
    
    return CreateSceneResponse(
        id=scene_id,
        chapter=request.chapter,
        order_in_chapter=request.order_in_chapter,
        path=str(scene_path),
        status="created"
    )

"""Codex management router for world-building items like characters, locations, etc."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from pathlib import Path
import yaml
import re

router = APIRouter(prefix="/codex", tags=["codex"])


class CodexItem(BaseModel):
    """Base model for codex items."""
    id: str
    name: str
    type: str  # "character", "location", "object", "organization", "event"
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Character(BaseModel):
    """Character codex item model."""
    id: str
    name: str
    age: Optional[int] = None
    occupation: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    voice: Optional[str] = None
    arc: Optional[str] = None
    appearance: Optional[str] = None
    relationships: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class Location(BaseModel):
    """Location codex item model."""
    id: str
    name: str
    type: Optional[str] = None  # "city", "building", "room", "outdoor", etc.
    description: Optional[str] = None
    atmosphere: Optional[str] = None
    significance: Optional[str] = None
    connected_locations: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class CreateCodexItemRequest(BaseModel):
    """Request model for creating a new codex item."""
    name: str
    type: str  # "character", "location", "object", "organization", "event"
    data: Dict[str, Any]  # Flexible data structure for different item types


class CreateCodexItemResponse(BaseModel):
    """Response model for codex item creation."""
    id: str
    name: str
    type: str
    path: str
    status: str


@router.get("/items", response_model=List[CodexItem])
async def list_codex_items(
    item_type: Optional[str] = Query(None, description="Filter by item type"),
    search: Optional[str] = Query(None, description="Search in item names or descriptions")
):
    """List all codex items with optional filtering."""
    items = []
    
    # Read from data/codex directory
    codex_dir = Path("data/codex")
    if codex_dir.exists():
        for md_file in codex_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse frontmatter if present
                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content) or {}
                
                item_name = metadata.get('name', md_file.stem)
                item_type_val = metadata.get('type', 'general')
                item_description = metadata.get('description', '')
                
                # Apply type filter if specified
                if item_type and item_type_val != item_type:
                    continue
                    
                # Apply search filter if specified
                if search and search.lower() not in item_name.lower() and search.lower() not in item_description.lower():
                    continue
                
                items.append(CodexItem(
                    id=md_file.stem,
                    name=item_name,
                    type=item_type_val,
                    description=item_description,
                    tags=metadata.get('tags', []),
                    metadata=metadata
                ))
            except Exception as e:
                print(f"Error parsing {md_file}: {e}")
                continue
    
    return items


@router.get("/items/{item_id}")
async def get_codex_item(item_id: str):
    """Get a specific codex item by ID."""
    item_path = Path(f"data/codex/{item_id}.md")
    
    if not item_path.exists():
        raise HTTPException(status_code=404, detail=f"Codex item {item_id} not found")
    
    content = item_path.read_text(encoding='utf-8')
    
    # Parse frontmatter and content
    metadata = {}
    text_content = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            yaml_content = parts[1]
            text_content = parts[2].strip()
            metadata = yaml.safe_load(yaml_content) or {}
    
    return {
        "id": item_id,
        "metadata": metadata,
        "content": text_content,
        "path": str(item_path)
    }


@router.post("/items", response_model=CreateCodexItemResponse)
async def create_codex_item(request: CreateCodexItemRequest):
    """Create a new codex item."""
    # Generate ID from name
    item_id = re.sub(r'[^a-zA-Z0-9_-]', '_', request.name.lower())
    
    # Create data/codex directory if it doesn't exist
    codex_dir = Path("data/codex")
    codex_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if item already exists
    item_path = codex_dir / f"{item_id}.md"
    if item_path.exists():
        raise HTTPException(status_code=409, detail=f"Codex item {item_id} already exists")
    
    # Prepare frontmatter
    frontmatter: Dict[str, Any] = {
        "name": request.name,
        "type": request.type,
    }
    
    # Add all data from request
    frontmatter.update(request.data)
    
    # Create markdown content with YAML frontmatter
    content_lines = ["---"]
    content_lines.append(yaml.dump(frontmatter, default_flow_style=False).strip())
    content_lines.append("---")
    content_lines.append(f"\n# {request.name}\n")
    
    # Add type-specific template content
    if request.type == "character":
        content_lines.append("## Character Details\n")
        content_lines.append("*Add character details here...*\n")
    elif request.type == "location":
        content_lines.append("## Location Details\n") 
        content_lines.append("*Add location details here...*\n")
    else:
        content_lines.append("## Details\n")
        content_lines.append("*Add details here...*\n")
    
    full_content = "\n".join(content_lines)
    
    # Write the file
    item_path.write_text(full_content, encoding='utf-8')
    
    return CreateCodexItemResponse(
        id=item_id,
        name=request.name,
        type=request.type,
        path=str(item_path),
        status="created"
    )


@router.get("/characters", response_model=List[Character])
async def list_characters():
    """List all character codex items."""
    characters = []
    
    codex_dir = Path("data/codex")
    if codex_dir.exists():
        for md_file in codex_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse frontmatter if present
                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content) or {}
                
                # Only include character items
                if metadata.get('type') == 'character':
                    characters.append(Character(
                        id=md_file.stem,
                        name=metadata.get('name', md_file.stem),
                        age=metadata.get('age'),
                        occupation=metadata.get('occupation'),
                        personality=metadata.get('personality'),
                        background=metadata.get('background'),
                        voice=metadata.get('voice'),
                        arc=metadata.get('arc'),
                        appearance=metadata.get('appearance'),
                        relationships=metadata.get('relationships', {}),
                        tags=metadata.get('tags', []),
                        notes=metadata.get('notes')
                    ))
            except Exception as e:
                print(f"Error parsing character {md_file}: {e}")
                continue
    
    return characters


@router.get("/locations", response_model=List[Location])
async def list_locations():
    """List all location codex items."""
    locations = []
    
    codex_dir = Path("data/codex")
    if codex_dir.exists():
        for md_file in codex_dir.glob("*.md"):
            if md_file.name.startswith('.'):
                continue
                
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse frontmatter if present
                metadata = {}
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content) or {}
                
                # Only include location items
                if metadata.get('type') == 'location':
                    locations.append(Location(
                        id=md_file.stem,
                        name=metadata.get('name', md_file.stem),
                        type=metadata.get('location_type'),
                        description=metadata.get('description'),
                        atmosphere=metadata.get('atmosphere'),
                        significance=metadata.get('significance'),
                        connected_locations=metadata.get('connected_locations', []),
                        tags=metadata.get('tags', []),
                        notes=metadata.get('notes')
                    ))
            except Exception as e:
                print(f"Error parsing location {md_file}: {e}")
                continue
    
    return locations
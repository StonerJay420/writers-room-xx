"""Ingest router for file uploads and indexing."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path
import frontmatter
import re
from sqlalchemy.orm import Session

from ..db import get_write_session
from ..models import Scene

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IndexRequest(BaseModel):
    paths: List[str]
    reindex: bool = False


class IndexResponse(BaseModel):
    scenes: int
    chunks: int
    status: str


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(..., description="Either 'manuscript' or 'codex'")
):
    """Upload a markdown file."""
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Only .md files are allowed")

    if file_type not in ['manuscript', 'codex']:
        raise HTTPException(status_code=400, detail="file_type must be 'manuscript' or 'codex'")

    # Create target directory
    target_dir = Path(f"data/{file_type}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = target_dir / file.filename
    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "path": str(file_path),
        "type": file_type,
        "status": "uploaded"
    }


@router.post("/index", response_model=IndexResponse)
async def index_files(
    request: IndexRequest,
    db: Session = Depends(get_write_session)
) -> IndexResponse:
    """Index markdown files into the database."""
    scenes_count = 0

    for path_str in request.paths:
        path = Path(path_str)
        if not path.exists():
            continue

        # Find all .md files
        md_files = list(path.glob("**/*.md"))

        for md_file in md_files:
            if md_file.name.startswith('.'):
                continue

            # Parse the markdown file
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Extract metadata from frontmatter or filename
                metadata = post.metadata

                # Generate scene ID from filename
                scene_id = md_file.stem

                # Extract chapter and scene numbers from filename or metadata
                chapter = metadata.get('chapter', 1)
                order_in_chapter = metadata.get('scene', 1)

                # Try to extract from filename pattern like "ch01_s02"
                match = re.match(r'ch(\d+)_s(\d+)', scene_id)
                if match:
                    chapter = int(match.group(1))
                    order_in_chapter = int(match.group(2))

                # Check if scene already exists
                existing = db.query(Scene).filter(Scene.id == scene_id).first()

                if existing and not request.reindex:
                    continue

                # Create or update scene
                scene_data = {
                    'id': scene_id,
                    'chapter': chapter,
                    'order_in_chapter': order_in_chapter,
                    'pov': metadata.get('pov'),
                    'location': metadata.get('location'),
                    'text_path': str(md_file.absolute()),
                    'beats_json': metadata.get('beats', {}),
                    'links_json': metadata.get('links', {})
                }

                if existing:
                    # Update existing
                    for key, value in scene_data.items():
                        if key != 'id':  # Don't update the ID
                            setattr(existing, key, value)
                else:
                    # Create new
                    scene = Scene(**scene_data)
                    db.add(scene)

                scenes_count += 1

            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                continue

    db.commit()

    return IndexResponse(
        scenes=scenes_count,
        chunks=scenes_count,  # For now, assume 1 chunk per scene
        status="completed"
    )


@router.get("/")
async def ingest_status():
    """Get ingest status."""
    return {"status": "ingest service ready"}
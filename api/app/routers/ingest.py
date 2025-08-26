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
from ..rag.chroma_client import get_chroma_client
from ..rag.embeddings import embed_texts
from ..rag.chunker import chunk_markdown

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
    """Upload a manuscript file in various formats."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check supported file formats
    supported_formats = ['.md', '.txt', '.docx', '.rtf', '.doc']
    is_supported = any(file.filename.lower().endswith(fmt) for fmt in supported_formats)
    
    if not is_supported:
        raise HTTPException(status_code=400, detail="Supported formats: .md, .txt, .docx, .rtf, .doc")

    if file_type not in ['manuscript', 'codex']:
        raise HTTPException(status_code=400, detail="file_type must be 'manuscript' or 'codex'")

    # Create target directory
    target_dir = Path(f"data/{file_type}")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Save file with content processing
    file_path = target_dir / file.filename
    
    # Read and process file content based on format
    content = await file.read()
    
    # For non-markdown files, we might need conversion
    # For now, save the file as-is and let the indexing process handle conversion
    with open(file_path, 'wb') as buffer:
        buffer.write(content)

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
    """Index markdown files into the database and ChromaDB."""
    scenes_count = 0
    chunks_count = 0
    chroma_client = get_chroma_client()

    for path_str in request.paths:
        path = Path(path_str)
        if not path.exists():
            continue

        # Determine collection name based on path
        collection_name = "codex_docs" if "codex" in path_str else "manuscript_scenes"

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
                content = post.content

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

                # Only create database records for manuscript scenes
                if "manuscript" in path_str:
                    # Check if scene already exists
                    existing = db.query(Scene).filter(Scene.id == scene_id).first()

                    if not existing or request.reindex:
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

                # Chunk the content for RAG
                chunks = chunk_markdown(content, max_tokens=800, stride=200)
                
                # Process chunks for embeddings
                if chunks:
                    chunk_texts = [chunk["text"] for chunk in chunks]
                    embeddings = embed_texts(chunk_texts)
                    
                    # Prepare metadata for ChromaDB
                    chunk_ids = []
                    chunk_metadatas = []
                    
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{scene_id}_chunk_{i}"
                        chunk_ids.append(chunk_id)
                        
                        chunk_metadata = {
                            "source_path": str(md_file),
                            "scene_id": scene_id if "manuscript" in path_str else None,
                            "chapter": chapter if "manuscript" in path_str else None,
                            "start_line": chunk.get("start_line", 0),
                            "end_line": chunk.get("end_line", 0),
                            "token_count": chunk.get("token_count", 0),
                            "collection_type": collection_name
                        }
                        
                        # Add frontmatter metadata
                        for key, value in metadata.items():
                            if key not in chunk_metadata and isinstance(value, (str, int, float, bool)):
                                chunk_metadata[key] = value
                        
                        chunk_metadatas.append(chunk_metadata)
                    
                    # Upsert to ChromaDB
                    chroma_client.upsert(
                        collection=collection_name,
                        embeddings=embeddings,
                        metadatas=chunk_metadatas,
                        ids=chunk_ids
                    )
                    
                    chunks_count += len(chunks)

            except Exception as e:
                print(f"Error processing {md_file}: {e}")
                continue

    db.commit()

    return IndexResponse(
        scenes=scenes_count,
        chunks=chunks_count,
        status="completed"
    )


@router.get("/")
async def ingest_status():
    """Get ingest status."""
    return {"status": "ingest service ready"}
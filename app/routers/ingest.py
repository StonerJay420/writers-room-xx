from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Scene, Character
from app.services.file_service import file_service
from app.services.lore_service import lore_service
from typing import List
import json

router = APIRouter()

@router.post("/ingest/index")
async def index_files(
    paths: List[str] | None = None,
    reindex: bool = False,
    db: Session = Depends(get_db)
):
    """Index manuscript and codex files"""
    try:
        if not paths:
            paths = ["data/manuscript", "data/codex"]
        
        # Discover files
        files = await file_service.discover_files(paths)
        
        if not files:
            raise HTTPException(status_code=404, detail="No markdown files found in specified paths")
        
        indexed_docs = 0
        scenes_count = 0
        
        # Process manuscript files
        manuscript_files = [f for f in files if "manuscript" in str(f)]
        codex_files = [f for f in files if "codex" in str(f)]
        
        # Index scenes
        for file_path in manuscript_files:
            try:
                scene_meta, content = await file_service.parse_scene(file_path)
                
                # Check if scene exists
                existing_scene = db.query(Scene).filter(Scene.id == scene_meta["id"]).first()
                
                if existing_scene and not reindex:
                    continue
                
                if existing_scene:
                    # Update existing scene
                    existing_scene.chapter = scene_meta.get("chapter")
                    existing_scene.order_in_chapter = scene_meta.get("order_in_chapter") 
                    existing_scene.pov = scene_meta.get("pov")
                    existing_scene.location = scene_meta.get("location")
                    existing_scene.text_path = scene_meta.get("text_path")
                    existing_scene.beats_json = scene_meta.get("beats_json")
                    existing_scene.links_json = scene_meta.get("links_json")
                    existing_scene.content = content
                else:
                    # Create new scene
                    scene = Scene(
                        content=content,
                        **scene_meta
                    )
                    db.add(scene)
                
                scenes_count += 1
                indexed_docs += 1
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        # Read codex content for lore service
        codex_content = await file_service.read_codex_files()
        lore_service.build_registries(codex_content)
        
        indexed_docs += len(codex_files)
        
        db.commit()
        
        return {
            "indexed_docs": indexed_docs,
            "scenes": scenes_count,
            "codex_files": len(codex_files),
            "status": "success"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.post("/ingest/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "manuscript",
    db: Session = Depends(get_db)
):
    """Upload a single file to manuscript or codex"""
    try:
        if not file.filename or not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only markdown files are supported")
        
        # Determine target directory
        if file_type == "manuscript":
            target_dir = file_service.manuscript_path
        elif file_type == "codex":
            target_dir = file_service.codex_path
        else:
            raise HTTPException(status_code=400, detail="file_type must be 'manuscript' or 'codex'")
        
        # Save file
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = file.filename or "unknown.md"
        file_path = target_dir / filename
        
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # If it's a manuscript file, parse and index it
        if file_type == "manuscript":
            scene_meta, text_content = await file_service.parse_scene(file_path)
            
            scene = Scene(
                content=text_content,
                **scene_meta
            )
            db.add(scene)
            db.commit()
            
            return {
                "message": "File uploaded and indexed",
                "scene_id": scene_meta["id"],
                "file_path": str(file_path)
            }
        else:
            # Rebuild lore registries for codex files
            codex_content = await file_service.read_codex_files()
            lore_service.build_registries(codex_content)
            
            return {
                "message": "Codex file uploaded",
                "file_path": str(file_path)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

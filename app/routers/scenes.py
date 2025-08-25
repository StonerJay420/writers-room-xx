from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Scene
from typing import List, Optional

router = APIRouter()

@router.get("/scenes")
async def list_scenes(
    chapter: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List scenes with optional filtering"""
    try:
        query = db.query(Scene)
        
        if chapter is not None:
            query = query.filter(Scene.chapter == chapter)
        
        if search:
            query = query.filter(Scene.content.contains(search))
        
        scenes = query.order_by(Scene.chapter, Scene.order_in_chapter).all()
        
        return [
            {
                "id": scene.id,
                "chapter": scene.chapter,
                "order_in_chapter": scene.order_in_chapter,
                "pov": scene.pov,
                "location": scene.location,
                "word_count": len(str(scene.content or "").split()),
                "created_at": scene.created_at,
                "updated_at": scene.updated_at
            }
            for scene in scenes
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scenes: {str(e)}")

@router.get("/scenes/{scene_id}")
async def get_scene(scene_id: str, db: Session = Depends(get_db)):
    """Get a specific scene with full content"""
    try:
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        return {
            "meta": {
                "id": scene.id,
                "chapter": scene.chapter,
                "order_in_chapter": scene.order_in_chapter,
                "pov": scene.pov,
                "location": scene.location,
                "text_path": scene.text_path,
                "beats_json": scene.beats_json,
                "links_json": scene.links_json,
                "created_at": scene.created_at,
                "updated_at": scene.updated_at
            },
            "content": scene.content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scene: {str(e)}")

@router.get("/scenes/{scene_id}/stats")
async def get_scene_stats(scene_id: str, db: Session = Depends(get_db)):
    """Get basic statistics for a scene"""
    try:
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        content = str(scene.content or "")
        words = content.split()
        sentences = content.split('.') + content.split('!') + content.split('?')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            "scene_id": scene_id,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "character_count": len(content),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}")

"""Diff and patch visualization router."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db import get_read_session
from ..models import Scene, Artifact, Job
from ..services.diff_service import diff_service


router = APIRouter(prefix="/diff", tags=["diff"])


class DiffRequest(BaseModel):
    """Request to generate diff between texts."""
    original: str
    modified: str
    filename: Optional[str] = "scene.txt"
    context_lines: int = 3


class DiffResponse(BaseModel):
    """Diff response model."""
    unified_diff: str
    additions: int
    deletions: int
    changes: int
    hunks: List[Dict[str, Any]]


class SideBySideRequest(BaseModel):
    """Request for side-by-side diff."""
    original: str
    modified: str
    width: int = 80


class SideBySideResponse(BaseModel):
    """Side-by-side diff response."""
    lines: List[Dict[str, str]]


@router.post("/generate", response_model=DiffResponse)
async def generate_diff(request: DiffRequest):
    """Generate unified diff between two texts."""
    
    try:
        diff_result = diff_service.generate_unified_diff(
            request.original,
            request.modified,
            request.filename or "scene.txt"
        )
        
        return DiffResponse(
            unified_diff=diff_result.unified_diff,
            additions=diff_result.additions,
            deletions=diff_result.deletions,
            changes=diff_result.changes,
            hunks=[hunk for hunk in diff_result.hunks]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/side-by-side", response_model=SideBySideResponse)
async def generate_side_by_side(request: SideBySideRequest):
    """Generate side-by-side diff view."""
    
    try:
        lines = diff_service.generate_side_by_side(
            request.original,
            request.modified,
            request.width
        )
        
        formatted_lines = []
        for left, right, change_type in lines:
            formatted_lines.append({
                "left": left,
                "right": right,
                "type": change_type
            })
        
        return SideBySideResponse(lines=formatted_lines)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scene/{scene_id}/variants")
async def get_scene_variants(
    scene_id: str,
    db: Session = Depends(get_read_session)
):
    """Get all variants for a scene with diffs."""
    
    # Get scene
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Read original content
    try:
        with open(scene.text_path, 'r') as f:
            original_text = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scene file not found")
    
    # Get all completed jobs for this scene
    jobs = db.query(Job).filter(
        Job.scene_id == scene_id,
        Job.status == "completed",
        Job.job_type == "agent_processing"
    ).all()
    
    variants = []
    
    for job in jobs:
        # Get artifacts for this job
        artifacts = db.query(Artifact).filter(Artifact.job_id == job.id).all()
        
        job_variants = {}
        
        for artifact in artifacts:
            if artifact.artifact_type == "agent_result":
                # Parse agent result
                import json
                try:
                    agent_data = json.loads(artifact.content)
                    variant_name = json.loads(artifact.metadata).get("variant", "unknown")
                    
                    if variant_name not in job_variants:
                        job_variants[variant_name] = {
                            "name": variant_name,
                            "agents": [],
                            "final_text": "",
                            "diff": None
                        }
                    
                    # Add agent result
                    job_variants[variant_name]["agents"].append({
                        "name": agent_data["agent_name"],
                        "model": agent_data["model_id"],
                        "confidence": agent_data["confidence_score"],
                        "reasoning": agent_data["reasoning"]
                    })
                    
                    # Use the last agent's result as final text
                    job_variants[variant_name]["final_text"] = agent_data["revised_text"]
                    
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Generate diffs for each variant
        for variant_name, variant_data in job_variants.items():
            if variant_data["final_text"]:
                diff_result = diff_service.generate_unified_diff(
                    original_text,
                    variant_data["final_text"],
                    f"{scene_id}_{variant_name}.md"
                )
                variant_data["diff"] = {
                    "additions": diff_result.additions,
                    "deletions": diff_result.deletions,
                    "changes": diff_result.changes,
                    "unified_diff": diff_result.unified_diff
                }
        
        variants.extend(job_variants.values())
    
    return {
        "scene_id": scene_id,
        "original_text": original_text,
        "variants": variants
    }


@router.post("/apply/{scene_id}")
async def apply_patch(
    scene_id: str,
    patch_text: str,
    db: Session = Depends(get_read_session)
):
    """Apply a patch to a scene (preview only - doesn't modify files)."""
    
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    try:
        with open(scene.text_path, 'r') as f:
            original_text = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scene file not found")
    
    # Apply patch
    success, patched_text, errors = diff_service.apply_patch(
        original_text, patch_text, fuzzy=True
    )
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to apply patch: {'; '.join(errors)}"
        )
    
    # Generate diff to show what changed
    preview_diff = diff_service.generate_unified_diff(
        original_text, patched_text, f"{scene_id}_preview.md"
    )
    
    return {
        "success": True,
        "preview_text": patched_text,
        "diff": {
            "additions": preview_diff.additions,
            "deletions": preview_diff.deletions,
            "changes": preview_diff.changes,
            "unified_diff": preview_diff.unified_diff
        }
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Scene, Job, Patch
from app.services.ai_service import ai_service
from app.services.file_service import file_service
from app.services.metrics_service import metrics_service
from app.services.diff_service import diff_service
from app.services.lore_service import lore_service
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json

router = APIRouter()

class PassRequest(BaseModel):
    scene_id: str
    agents: List[str] = ["lore_archivist", "grim_editor"]
    edge_intensity: int = 1

class PatchApplyRequest(BaseModel):
    scene_id: str
    variant: str
    commit_message: Optional[str] = None

@router.post("/passes/run")
async def run_pass(
    request: PassRequest,
    db: Session = Depends(get_db)
):
    """Run AI agents on a scene to generate patch suggestions"""
    try:
        # Get scene
        scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            scene_id=request.scene_id,
            status="running",
            agents_json=request.agents
        )
        db.add(job)
        db.commit()
        
        try:
            # Calculate initial metrics
            initial_metrics = metrics_service.calculate_metrics(str(scene.content))
            
            # Initialize result structure
            result = {
                "scene_id": request.scene_id,
                "variants": {},
                "reports": {
                    "metrics": {"before": initial_metrics},
                    "canon_receipts": [],
                    "rationales": {}
                }
            }
            
            # Run agents based on request
            suggestions = []
            lore_feedback = {"inconsistencies": [], "canon_references": []}
            
            if "grim_editor" in request.agents:
                # Generate line editing suggestions
                edit_result = await ai_service.generate_line_edits(
                    str(scene.content),
                    style_guidelines={}
                )
                
                if "suggestions" in edit_result:
                    suggestions = edit_result["suggestions"]
                    result["reports"]["rationales"]["grim_editor"] = edit_result.get("overall_rationale", "")
            
            if "lore_archivist" in request.agents:
                # Check lore consistency
                codex_content = await file_service.read_codex_files()
                lore_result = await ai_service.check_lore_consistency(
                    str(scene.content),
                    codex_content
                )
                
                lore_feedback = lore_result
                result["reports"]["rationales"]["lore_archivist"] = "Performed lore consistency check"
                
                # Generate canon receipts
                canon_receipts = lore_service.get_canon_receipts(str(scene.content))
                result["reports"]["canon_receipts"] = canon_receipts
            
            # Generate patch variants
            variants_to_create = ["safe"]
            if request.edge_intensity > 1:
                variants_to_create.append("bold")
            
            for variant in variants_to_create:
                if variant == "safe":
                    # Apply conservative suggestions
                    safe_suggestions = [s for s in suggestions if "conservative" in s.get("rationale", "").lower() or len(s.get("suggested", "")) < len(s.get("original", "")) * 1.2]
                    modified_text = diff_service.apply_suggestions(str(scene.content), safe_suggestions[:3])
                elif variant == "bold":
                    # Apply all suggestions
                    modified_text = diff_service.apply_suggestions(str(scene.content), suggestions)
                else:
                    modified_text = str(scene.content)
                
                # Generate diff
                diff_content = diff_service.generate_unified_diff(
                    str(scene.content),
                    modified_text,
                    f"{request.scene_id}.md"
                )
                
                # Calculate metrics for modified text
                modified_metrics = metrics_service.calculate_metrics(modified_text)
                
                # Create patch record
                patch_id = str(uuid.uuid4())
                patch = Patch(
                    id=patch_id,
                    scene_id=request.scene_id,
                    variant=variant,
                    diff_content=diff_content,
                    metrics_before=initial_metrics,
                    metrics_after=modified_metrics,
                    canon_receipts=result["reports"]["canon_receipts"],
                    rationale=result["reports"]["rationales"].get("grim_editor", "")
                )
                db.add(patch)
                
                # Add to result
                result["variants"][variant] = {
                    "patch_id": patch_id,
                    "diff": diff_content,
                    "metrics_after": modified_metrics,
                    "summary": diff_service.extract_changes_summary(diff_content)
                }
            
            # Update job with results
            db.query(Job).filter(Job.id == job_id).update({"status": "done", "result_json": result})
            db.commit()
            
            return {"job_id": job_id, "status": "completed", "result": result}
            
        except Exception as e:
            db.query(Job).filter(Job.id == job_id).update({"status": "error", "result_json": {"error": str(e)}})
            db.commit()
            raise HTTPException(status_code=500, detail=f"Pass execution failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pass: {str(e)}")

@router.get("/passes/{job_id}/result")
async def get_pass_result(job_id: str, db: Session = Depends(get_db)):
    """Get the result of a completed pass"""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job_id,
            "status": job.status,
            "result": job.result_json,
            "created_at": job.created_at,
            "updated_at": job.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve result: {str(e)}")

@router.post("/patches/apply")
async def apply_patch(
    request: PatchApplyRequest,
    db: Session = Depends(get_db)
):
    """Apply a selected patch to the scene file"""
    try:
        # Get the patch
        patch = db.query(Patch).filter(
            Patch.scene_id == request.scene_id,
            Patch.variant == request.variant
        ).first()
        
        if not patch:
            raise HTTPException(status_code=404, detail="Patch not found")
        
        # Get the scene
        scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        # Apply the diff to get the new content
        # For simplicity, we'll reconstruct the modified text from the patch
        # In a real implementation, you'd apply the unified diff properly
        
        # Get the modified text from the diff (simplified approach)
        diff_lines = str(patch.diff_content).split('\n')
        modified_lines = []
        original_lines = str(scene.content).split('\n')
        
        # Simple diff application (this is a simplified version)
        for line in diff_lines:
            if line.startswith('+') and not line.startswith('+++'):
                modified_lines.append(line[1:])
            elif not line.startswith('-') and not line.startswith('---'):
                if line.startswith(' '):
                    modified_lines.append(line[1:])
        
        # If we have modified lines, reconstruct content
        if modified_lines:
            new_content = '\n'.join(modified_lines)
        else:
            # Fallback: use original content (patch might be empty)
            new_content = str(scene.content)
        
        # Update scene in database
        db.query(Scene).filter(Scene.id == request.scene_id).update({"content": new_content})
        db.commit()
        
        # Write to file
        success = await file_service.write_scene(request.scene_id, new_content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write scene to file")
        
        return {
            "status": "ok",
            "scene_id": request.scene_id,
            "variant": request.variant,
            "message": f"Applied {request.variant} patch to {request.scene_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply patch: {str(e)}")

@router.get("/patches/{scene_id}")
async def list_patches(scene_id: str, db: Session = Depends(get_db)):
    """List all patches for a scene"""
    try:
        patches = db.query(Patch).filter(Patch.scene_id == scene_id).all()
        
        return [
            {
                "id": patch.id,
                "scene_id": patch.scene_id,
                "variant": patch.variant,
                "metrics_summary": {
                    "before": {},
                    "after": {}
                },
                "changes_summary": diff_service.extract_changes_summary(str(patch.diff_content or "")),
                "canon_receipts_count": 0,
                "created_at": patch.created_at
            }
            for patch in patches
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patches: {str(e)}")

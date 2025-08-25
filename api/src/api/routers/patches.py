"""Patches router for managing AI agent processing and diff generation."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import json
import uuid

from ..db import get_write_session, get_read_session
from ..models import Scene, Job, Artifact
from ..services.ai_service import ai_service
from ..routers.models import model_preferences


router = APIRouter(prefix="/patches", tags=["patches"])


class AgentPassRequest(BaseModel):
    """Request to run agents on a scene."""
    scene_id: str
    agents: List[str] = ["lore_archivist", "grim_editor"]
    custom_models: Optional[Dict[str, str]] = None  # Agent name -> model ID
    variants: List[str] = ["safe", "bold"]


class PatchResponse(BaseModel):
    """Response containing generated patches."""
    job_id: str
    scene_id: str
    status: str
    patches: List[Dict[str, Any]]
    cost_usd: float


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    scene_id: str
    result: Optional[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]


@router.post("/generate", response_model=PatchResponse)
async def generate_patches(
    request: AgentPassRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_write_session)
):
    """Generate patches for a scene using specified agents."""
    
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {request.scene_id} not found")
    
    # Read scene text
    scene_text = ""
    if scene.text_path:
        try:
            with open(scene.text_path, 'r') as f:
                content = f.read()
                # Remove front matter if present
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        scene_text = parts[2].strip()
                else:
                    scene_text = content
        except:
            raise HTTPException(status_code=500, detail="Could not read scene text")
    
    # Create job
    job = Job(
        id=str(uuid.uuid4()),
        scene_id=request.scene_id,
        status="running",
        agents_json={"agents": request.agents, "variants": request.variants}
    )
    db.add(job)
    db.commit()
    
    # Process with agents
    patches = []
    total_cost = 0.0
    
    for agent_name in request.agents:
        # Get custom model if specified
        custom_model = None
        if request.custom_models and agent_name in request.custom_models:
            custom_model = request.custom_models[agent_name]
        
        # Call agent
        result = await ai_service.call_agent(
            agent_name=agent_name,
            prompt=f"Analyze this scene and provide specific editing suggestions.",
            scene_text=scene_text,
            custom_model=custom_model
        )
        
        if "error" in result:
            continue
        
        # Create artifacts for each variant
        for variant in request.variants:
            artifact = Artifact(
                id=str(uuid.uuid4()),
                scene_id=request.scene_id,
                variant=variant,
                diff_key=f"diffs/{job.id}/{agent_name}_{variant}.diff",
                metrics_before={},
                metrics_after={},
                receipts_json={
                    "agent": agent_name,
                    "model": result.get("model"),
                    "cost": result.get("cost_usd", 0),
                    "timestamp": result.get("timestamp")
                }
            )
            db.add(artifact)
            
            patches.append({
                "agent": agent_name,
                "variant": variant,
                "suggestions": result.get("response"),
                "model_used": result.get("model"),
                "cost": result.get("cost_usd", 0)
            })
        
        total_cost += result.get("cost_usd", 0)
    
    # Update job status
    job.status = "done"
    job.result_json = {"patches": patches, "total_cost": total_cost}
    job.updated_at = datetime.utcnow()
    db.commit()
    
    return PatchResponse(
        job_id=job.id,
        scene_id=request.scene_id,
        status="completed",
        patches=patches,
        cost_usd=total_cost
    )


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_read_session)
):
    """Get status of a patch generation job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatus(
        job_id=job.id,
        status=job.status,
        scene_id=job.scene_id,
        result=job.result_json,
        created_at=job.created_at.isoformat() if job.created_at else "",
        updated_at=job.updated_at.isoformat() if job.updated_at else None
    )


@router.get("/scene/{scene_id}/patches")
async def get_scene_patches(
    scene_id: str,
    db: Session = Depends(get_read_session)
):
    """Get all patches generated for a scene."""
    artifacts = db.query(Artifact).filter(Artifact.scene_id == scene_id).all()
    
    patches = []
    for artifact in artifacts:
        patches.append({
            "id": artifact.id,
            "variant": artifact.variant,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else "",
            "receipts": artifact.receipts_json
        })
    
    return {"scene_id": scene_id, "patches": patches}
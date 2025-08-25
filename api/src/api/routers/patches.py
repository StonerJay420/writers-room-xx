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
from ..services.agent_service import agent_service
from ..services.job_queue import job_queue
from ..routers.models import model_preferences


router = APIRouter(prefix="/patches", tags=["patches"])


class PatchRequest(BaseModel):
    """Request to generate patches for a scene."""
    scene_id: str
    agents: List[str] = ["lore_archivist", "grim_editor"]
    variants: List[str] = ["safe", "bold"]
    custom_instructions: Optional[str] = None


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
    request: PatchRequest,
    db: Session = Depends(get_write_session)
):
    """Generate patches for a scene using AI agents."""
    
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    try:
        # Process with agent service
        result = await agent_service.process_scene(
            request.scene_id,
            request.variants,
            request.custom_instructions
        )
        
        # Convert agent results to patches format
        patches = []
        for variant in result["variants"]:
            variant_data = {
                "variant": variant["variant_name"],
                "agents": [],
                "final_text": variant["final_text"],
                "improvement_score": variant["improvement_score"],
                "total_changes": variant["total_changes"]
            }
            
            for agent_result in variant["agent_results"]:
                variant_data["agents"].append({
                    "name": agent_result.agent_name,
                    "model": agent_result.model_id,
                    "confidence": agent_result.confidence_score,
                    "reasoning": agent_result.reasoning,
                    "cost": agent_result.cost_usd
                })
            
            patches.append(variant_data)
        
        return PatchResponse(
            job_id=result["job_id"],
            scene_id=request.scene_id,
            status="completed",
            patches=patches,
            cost_usd=result["total_cost"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
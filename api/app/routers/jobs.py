"""Background job management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from ..auth import get_current_user, require_rate_limit, get_user_llm_client
from ..background import job_queue

router = APIRouter(prefix="/jobs", tags=["background-jobs"])
logger = logging.getLogger(__name__)


class JobRequest(BaseModel):
    """Request to create a background job."""
    type: str = Field(description="Job type (agent_pass, bulk_ingest)")
    payload: Dict[str, Any] = Field(description="Job payload data")
    priority: int = Field(default=0, description="Job priority (higher = more urgent)")


class JobResponse(BaseModel):
    """Response with job information."""
    job_id: str = Field(description="Unique job identifier")
    type: str = Field(description="Job type")
    status: str = Field(description="Job status")
    message: str = Field(description="Status message")


class JobStatusResponse(BaseModel):
    """Detailed job status response."""
    job_id: str = Field(description="Job identifier")
    type: str = Field(description="Job type")
    status: str = Field(description="Current status")
    created_at: str = Field(description="Creation timestamp")
    started_at: Optional[str] = Field(description="Start timestamp")
    completed_at: Optional[str] = Field(description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(description="Job result")
    error: Optional[str] = Field(description="Error message if failed")
    retry_count: int = Field(description="Number of retries")


@router.post("/create", response_model=JobResponse)
async def create_job(
    request: JobRequest,
    user: dict = Depends(require_rate_limit(limit=30, window=60)),
    llm_client = Depends(get_user_llm_client)
):
    """
    Create a new background job.
    
    Supports job types:
    - agent_pass: Run agent processing on a scene
    - bulk_ingest: Process multiple files in background
    """
    try:
        # Add user's LLM key to payload if available
        if hasattr(llm_client, 'api_key') and llm_client.api_key:
            request.payload["user_llm_key"] = llm_client.api_key
        
        # Validate job type
        if request.type not in ["agent_pass", "bulk_ingest"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported job type: {request.type}"
            )
        
        # Create the job
        job_id = await job_queue.enqueue(
            job_type=request.type,
            payload=request.payload,
            priority=request.priority
        )
        
        logger.info(f"Created job {job_id} for user {user['name']}")
        
        return JobResponse(
            job_id=job_id,
            type=request.type,
            status="queued",
            message="Job created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get the status of a background job.
    
    Returns detailed information about job progress and results.
    """
    try:
        job_data = await job_queue.get_job_status(job_id)
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return JobStatusResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.post("/agent-pass", response_model=JobResponse)
async def create_agent_pass_job(
    scene_id: str,
    agents: List[str] = ["grim_editor", "tone_metrics"],
    user: dict = Depends(require_rate_limit(limit=10, window=60)),
    llm_client = Depends(get_user_llm_client)
):
    """
    Create a background job to run agent processing on a scene.
    
    This is useful for long-running agent passes that shouldn't block
    the API response.
    """
    try:
        # Prepare job payload
        payload = {
            "scene_id": scene_id,
            "agents": agents
        }
        
        # Add user's LLM key if available
        if hasattr(llm_client, 'api_key') and llm_client.api_key:
            payload["user_llm_key"] = llm_client.api_key
        
        # Create the job
        job_id = await job_queue.enqueue(
            job_type="agent_pass",
            payload=payload,
            priority=1  # Higher priority for agent passes
        )
        
        logger.info(f"Created agent pass job {job_id} for scene {scene_id}")
        
        return JobResponse(
            job_id=job_id,
            type="agent_pass",
            status="queued",
            message=f"Agent pass job created for scene {scene_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to create agent pass job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent pass job"
        )
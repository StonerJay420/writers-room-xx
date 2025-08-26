"""Background job processing with Redis."""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """Background job definition."""
    id: str
    type: str
    payload: Dict[str, Any]
    status: str = "queued"  # queued, running, completed, failed
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class JobQueue:
    """Redis-based job queue for background processing."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.job_handlers: Dict[str, Callable] = {}
        self.running = False
        
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a job handler function."""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    async def enqueue(self, job_type: str, payload: Dict[str, Any], priority: int = 0) -> str:
        """Add a job to the queue."""
        job = Job(
            id=str(uuid4()),
            type=job_type,
            payload=payload
        )
        
        if not self.redis_client:
            # Fallback: execute immediately if Redis unavailable
            logger.warning("Redis unavailable, executing job immediately")
            return await self._execute_job_immediately(job)
        
        try:
            # Store job data
            await self.redis_client.hset(
                f"job:{job.id}",
                mapping={
                    "data": json.dumps(asdict(job)),
                    "priority": priority
                }
            )
            
            # Add to queue
            await self.redis_client.zadd("job_queue", {job.id: priority})
            
            logger.info(f"Enqueued job {job.id} of type {job_type}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            # Fallback: execute immediately
            return await self._execute_job_immediately(job)
    
    async def _execute_job_immediately(self, job: Job) -> str:
        """Execute job immediately as fallback."""
        handler = self.job_handlers.get(job.type)
        if not handler:
            logger.error(f"No handler for job type: {job.type}")
            return job.id
        
        try:
            job.status = "running"
            job.started_at = datetime.utcnow().isoformat()
            
            result = await handler(job.payload)
            
            job.status = "completed"
            job.completed_at = datetime.utcnow().isoformat()
            job.result = result
            
            logger.info(f"Completed job {job.id} immediately")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow().isoformat()
            logger.error(f"Job {job.id} failed: {e}")
        
        return job.id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and result."""
        if not self.redis_client:
            return {"status": "unknown", "message": "Redis unavailable"}
        
        try:
            job_data = await self.redis_client.hget(f"job:{job_id}", "data")
            if job_data:
                return json.loads(job_data)
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
        
        return None
    
    async def start_worker(self):
        """Start the background job worker."""
        if not self.redis_client:
            logger.warning("Cannot start worker - Redis unavailable")
            return
        
        self.running = True
        logger.info("Starting background job worker")
        
        while self.running:
            try:
                # Get next job from queue (blocking pop with timeout)
                result = await self.redis_client.bzpopmin("job_queue", timeout=5)
                
                if not result:
                    continue  # Timeout, check if still running
                
                queue_name, job_id, priority = result
                job_id = job_id.decode('utf-8')
                
                # Get job data
                job_data = await self.redis_client.hget(f"job:{job_id}", "data")
                if not job_data:
                    logger.warning(f"Job {job_id} not found")
                    continue
                
                job_dict = json.loads(job_data)
                job = Job(**job_dict)
                
                # Execute job
                await self._execute_job(job)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
        
        logger.info("Background job worker stopped")
    
    async def _execute_job(self, job: Job):
        """Execute a single job."""
        handler = self.job_handlers.get(job.type)
        if not handler:
            logger.error(f"No handler for job type: {job.type}")
            job.status = "failed"
            job.error = f"No handler for job type: {job.type}"
            await self._update_job(job)
            return
        
        try:
            job.status = "running"
            job.started_at = datetime.utcnow().isoformat()
            await self._update_job(job)
            
            logger.info(f"Executing job {job.id} of type {job.type}")
            
            # Execute the handler
            result = await handler(job.payload)
            
            job.status = "completed"
            job.completed_at = datetime.utcnow().isoformat()
            job.result = result
            
            logger.info(f"Completed job {job.id}")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow().isoformat()
            job.retry_count += 1
            
            logger.error(f"Job {job.id} failed: {e}")
            
            # Retry if under limit
            if job.retry_count < job.max_retries:
                job.status = "queued"
                await self.redis_client.zadd("job_queue", {job.id: 0})
                logger.info(f"Retrying job {job.id} (attempt {job.retry_count + 1})")
        
        await self._update_job(job)
    
    async def _update_job(self, job: Job):
        """Update job in Redis."""
        if self.redis_client:
            await self.redis_client.hset(
                f"job:{job.id}",
                "data",
                json.dumps(asdict(job))
            )
    
    async def stop_worker(self):
        """Stop the background worker."""
        self.running = False
        logger.info("Stopping background job worker")


# Global job queue instance
job_queue = JobQueue()


# Job handler functions
async def process_agent_pass(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process an agent pass job."""
    from .routers.passes import run_agent_pass_internal
    
    scene_id = payload.get("scene_id")
    agents = payload.get("agents", [])
    user_llm_key = payload.get("user_llm_key")
    
    if not scene_id:
        raise ValueError("scene_id required")
    
    # Set up LLM client with user's key
    from .services.llm_client import LLMClient
    if user_llm_key:
        llm_client = LLMClient(api_key=user_llm_key)
    else:
        llm_client = LLMClient()  # Disabled client
    
    # Execute the agent pass
    results = await run_agent_pass_internal(scene_id, agents, llm_client)
    
    return {
        "scene_id": scene_id,
        "agents_executed": len(agents),
        "results": results
    }


async def process_bulk_ingest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process bulk file ingestion job."""
    from .routers.ingest import process_files_internal
    
    file_paths = payload.get("file_paths", [])
    
    if not file_paths:
        raise ValueError("file_paths required")
    
    results = await process_files_internal(file_paths)
    
    return {
        "files_processed": len(file_paths),
        "results": results
    }


# Register job handlers
job_queue.register_handler("agent_pass", process_agent_pass)
job_queue.register_handler("bulk_ingest", process_bulk_ingest)
"""Job queue system for async processing."""
import asyncio
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import threading
import logging
from queue import Queue, PriorityQueue
import time

from ..models import Job
from ..db import get_write_session
from .agent_service import agent_service


logger = logging.getLogger(__name__)


@dataclass
class QueuedJob:
    """A job in the processing queue."""
    id: str
    priority: int
    job_type: str
    scene_id: str
    parameters: Dict[str, Any]
    created_at: datetime
    max_retries: int = 3
    retry_count: int = 0
    
    def __lt__(self, other):
        # Higher priority numbers = higher priority
        return self.priority > other.priority


class JobQueue:
    """Async job processing queue."""
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.queue = PriorityQueue()
        self.active_jobs: Dict[str, QueuedJob] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self.register_handler("agent_processing", self._handle_agent_processing)
        self.register_handler("metrics_calculation", self._handle_metrics_calculation)
    
    def start(self):
        """Start the job processing workers."""
        if self.running:
            return
        
        self.running = True
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} job workers")
    
    def stop(self):
        """Stop the job processing workers."""
        self.running = False
        
        # Add sentinel values to wake up workers
        for _ in range(self.max_workers):
            self.queue.put((0, None))
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("Stopped all job workers")
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler for a specific job type."""
        self.handlers[job_type] = handler
    
    def enqueue_job(
        self,
        job_type: str,
        scene_id: str,
        parameters: Dict[str, Any],
        priority: int = 1,
        max_retries: int = 3
    ) -> str:
        """Add a job to the queue."""
        
        # Create database job record
        with get_write_session() as db:
            job = Job(
                scene_id=scene_id,
                job_type=job_type,
                status="queued",
                request_data=json.dumps(parameters)
            )
            db.add(job)
            db.commit()
            
            job_id = job.id
        
        # Create queued job
        queued_job = QueuedJob(
            id=job_id,
            priority=priority,
            job_type=job_type,
            scene_id=scene_id,
            parameters=parameters,
            created_at=datetime.utcnow(),
            max_retries=max_retries
        )
        
        # Add to queue
        self.queue.put((priority, queued_job))
        
        logger.info(f"Enqueued job {job_id} for scene {scene_id}")
        return job_id
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "queue_size": self.queue.qsize(),
            "active_jobs": len(self.active_jobs),
            "workers": len(self.workers),
            "running": self.running
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        
        with get_write_session() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return None
            
            return {
                "id": job.id,
                "scene_id": job.scene_id,
                "job_type": job.job_type,
                "status": job.status,
                "cost_usd": job.cost_usd,
                "processing_time": job.processing_time,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
    
    def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                # Get next job (blocks until available)
                priority, queued_job = self.queue.get(timeout=1)
                
                # Check for sentinel value
                if queued_job is None:
                    break
                
                # Process the job
                self._process_job(queued_job)
                
            except Exception as e:
                if self.running:  # Don't log errors during shutdown
                    logger.error(f"Worker error: {e}")
                continue
    
    def _process_job(self, job: QueuedJob):
        """Process a single job."""
        job_id = job.id
        
        try:
            # Mark as active
            self.active_jobs[job_id] = job
            
            # Update database status
            with get_write_session() as db:
                db_job = db.query(Job).filter(Job.id == job_id).first()
                if db_job:
                    db_job.status = "running"
                    db.commit()
            
            logger.info(f"Processing job {job_id}: {job.job_type}")
            
            # Get handler
            handler = self.handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler for job type: {job.job_type}")
            
            # Execute handler
            start_time = time.time()
            result = handler(job)
            processing_time = time.time() - start_time
            
            # Update database with success
            with get_write_session() as db:
                db_job = db.query(Job).filter(Job.id == job_id).first()
                if db_job:
                    db_job.status = "completed"
                    db_job.processing_time = processing_time
                    db_job.completed_at = datetime.utcnow()
                    if isinstance(result, dict):
                        db_job.result_data = json.dumps(result)
                    db.commit()
            
            logger.info(f"Completed job {job_id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            
            # Handle retry
            job.retry_count += 1
            if job.retry_count < job.max_retries:
                # Re-queue with lower priority
                job.priority = max(job.priority - 1, 1)
                self.queue.put((job.priority, job))
                logger.info(f"Retrying job {job_id} (attempt {job.retry_count + 1})")
            else:
                # Mark as failed
                with get_write_session() as db:
                    db_job = db.query(Job).filter(Job.id == job_id).first()
                    if db_job:
                        db_job.status = "failed"
                        db_job.error_message = str(e)
                        db_job.completed_at = datetime.utcnow()
                        db.commit()
                
                logger.error(f"Job {job_id} failed permanently after {job.retry_count} retries")
        
        finally:
            # Remove from active jobs
            self.active_jobs.pop(job_id, None)
    
    async def _handle_agent_processing(self, job: QueuedJob) -> Dict[str, Any]:
        """Handle agent processing job."""
        
        parameters = job.parameters
        scene_id = job.scene_id
        variant_names = parameters.get("variants", ["safe", "bold"])
        custom_instructions = parameters.get("custom_instructions")
        
        # Call agent service
        result = await agent_service.process_scene(
            scene_id, variant_names, custom_instructions
        )
        
        return result
    
    def _handle_metrics_calculation(self, job: QueuedJob) -> Dict[str, Any]:
        """Handle metrics calculation job."""
        
        from .metrics_service import metrics_service
        from ..models import Scene
        
        scene_id = job.scene_id
        
        with get_write_session() as db:
            scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if not scene:
                raise ValueError(f"Scene {scene_id} not found")
            
            # Read scene content
            with open(scene.text_path, 'r') as f:
                text = f.read()
            
            # Calculate metrics
            metrics = metrics_service.calculate_metrics(text)
            feedback = metrics_service.generate_feedback(metrics)
            
            return {
                "scene_id": scene_id,
                "metrics": metrics.__dict__,
                "feedback": feedback
            }


# Global job queue instance
job_queue = JobQueue()

# Auto-start on import
job_queue.start()
"""RQ Worker for background job processing."""
import os
import sys
import redis
from rq import Worker, Queue, Connection
from rq.job import Job
import logging

# Add parent directory to path to import api modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.src.api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_redis_connection():
    """Create Redis connection from settings."""
    return redis.from_url(settings.redis_url)


def process_scene_job(job_id: str, scene_id: str, agents: list):
    """Process a scene with specified agents."""
    logger.info(f"Processing job {job_id} for scene {scene_id} with agents: {agents}")
    
    # TODO: Implement actual agent processing logic
    # This will be implemented in later prompts
    
    result = {
        "status": "completed",
        "scene_id": scene_id,
        "agents": agents,
        "patches": []
    }
    
    logger.info(f"Job {job_id} completed")
    return result


def main():
    """Main worker loop."""
    logger.info("Starting Writers Room X worker...")
    
    # Create Redis connection
    redis_conn = get_redis_connection()
    
    # Create queue
    queue = Queue("wrx", connection=redis_conn)
    
    # Create worker
    worker = Worker([queue], connection=redis_conn)
    
    logger.info(f"Worker connected to Redis at {settings.redis_url}")
    logger.info("Listening for jobs on queue: wrx")
    
    # Start worker
    worker.work()


if __name__ == "__main__":
    main()
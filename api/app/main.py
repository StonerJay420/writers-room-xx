"""Main FastAPI application."""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from .config import settings
from .db import init_database
from .utils.logging_config import setup_logging
from .middleware import setup_middleware
from .background import job_queue

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    setup_logging(log_level=settings.log_level)
    logger.info(f"Starting {settings.app_name}...")
    
    # Initialize database
    await init_database()
    
    # Connect to Redis for background jobs
    await job_queue.connect()
    
    # Log startup configuration
    logger.info("Configuration:")
    logger.info(f"  Debug mode: {settings.debug}")
    logger.info(f"  Database: {settings.database_url.split('://', 1)[0]}://...")
    logger.info(f"  Redis: {settings.redis_url}")
    logger.info(f"  OpenRouter API: {'configured' if settings.openrouter_api_key else 'BYOK mode'}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")
    await job_queue.disconnect()


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent AI system for manuscript editing with BYOK support",
    version="1.0.0",
    lifespan=lifespan
)

# Setup security middleware and CORS
setup_middleware(app)


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with system info."""
    return {
        "message": f"{settings.app_name} API",
        "version": "1.0.0",
        "status": "ok",
        "auth": "required",
        "byok": True,
        "documentation": "/docs"
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        # Test database connection
        from .db import get_read_session
        from sqlalchemy import text
        
        with get_read_session() as db:
            db.execute(text("SELECT 1"))
        
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    # Test Redis connection
    try:
        if job_queue.redis_client:
            await job_queue.redis_client.ping()
            redis_status = "ok"
        else:
            redis_status = "disconnected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "error"
    
    status = "ok" if db_status == "ok" else "degraded"
    
    return {
        "status": status,
        "database": db_status,
        "redis": redis_status,
        "background_jobs": "enabled" if redis_status == "ok" else "disabled"
    }


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Basic metrics endpoint."""
    try:
        from .auth import _api_keys, _user_llm_keys
        
        return {
            "active_sessions": len(_api_keys),
            "users_with_llm_keys": len(_user_llm_keys),
            "system_health": "ok"
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


# Import and include routers
from .routers.auth import router as auth_router
from .routers.jobs import router as jobs_router
from .routers.ingest import router as ingest_router
from .routers.scenes import router as scenes_router
from .routers.models import router as models_router
from .routers.patches import router as patches_router
from .routers.diff import router as diff_router
from .routers.reports import router as reports_router
from .routers.search import router as search_router
from .routers.passes import router as passes_router
from .routers.ai import router as ai_router

# Include routers
app.include_router(auth_router, prefix="/api")  # Auth first (no auth required)
app.include_router(jobs_router, prefix="/api")  # Background jobs

# Protected endpoints
from .routers.protected import router as protected_router
app.include_router(protected_router, prefix="/api")

# Core functionality endpoints (require auth)
app.include_router(ingest_router, prefix="/api")
app.include_router(scenes_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(patches_router, prefix="/api")
app.include_router(diff_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(passes_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
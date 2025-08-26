"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from .config import settings
from .db import init_database
from .utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    setup_logging(log_level=settings.log_level)
    print(f"Starting {settings.app_name}...")
    await init_database()
    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent AI system for manuscript editing",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": f"{settings.app_name} API",
        "status": "ok"
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Import and include routers
from .routers.ingest import router as ingest_router
from .routers.scenes import router as scenes_router
from .routers.models import router as models_router
from .routers.patches import router as patches_router
from .routers.diff import router as diff_router
from .routers.reports import router as reports_router
from .routers.search import router as search_router
from .routers.passes import router as passes_router

# Include routers
app.include_router(ingest_router, prefix="/api")
app.include_router(scenes_router, prefix="/api")
app.include_router(models_router, prefix="/api")
app.include_router(patches_router, prefix="/api")
app.include_router(diff_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(passes_router, prefix="/api")
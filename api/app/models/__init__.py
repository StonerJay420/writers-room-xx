"""SQLAlchemy models package."""
from sqlalchemy.ext.declarative import declarative_base

# Create Base class for all models
Base = declarative_base()

# Import all models to ensure they are registered with the metadata
from .scene import Scene
from .character import Character 
from .job import Job

__all__ = ["Base", "Scene", "Character", "Job"]
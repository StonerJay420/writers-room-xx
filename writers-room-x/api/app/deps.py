"""Dependency injection utilities."""
from typing import Generator
import chromadb
from sqlalchemy.orm import Session

from .db import SessionLocal
from .config import settings


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_settings():
    """Get application settings."""
    return settings


def get_chroma_client():
    """Get Chroma client."""
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port
    )
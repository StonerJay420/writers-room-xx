"""SQLAlchemy ORM models."""
from sqlalchemy import Column, String, Integer, Text, JSON, TIMESTAMP, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .db import Base

# Try to import pgvector if available
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    # Fallback for when pgvector is not available
    class Vector:
        def __init__(self, dim):
            self.dim = dim


class Scene(Base):
    """Scene model representing a chapter/scene in the manuscript."""
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)  # e.g., "ch02_s03"
    chapter = Column(Integer, nullable=False, index=True)
    order_in_chapter = Column(Integer, nullable=False)
    pov = Column(Text)
    location = Column(Text)
    text_path = Column(Text)  # Path to markdown file
    beats_json = Column(JSON)
    links_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="scene", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="scene", cascade="all, delete-orphan")
    embeddings = relationship("SceneEmbedding", back_populates="scene", cascade="all, delete-orphan")


class Character(Base):
    """Character model for tracking character information."""
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)  # e.g., "char:MC"
    name = Column(Text, nullable=False)
    voice_tags_json = Column(JSON)
    preferred_words_json = Column(JSON)
    banned_words_json = Column(JSON)
    arc_flags_json = Column(JSON)
    canon_quotes_json = Column(JSON)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())


class Job(Base):
    """Job model for tracking agent processing."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="queued")  # queued|running|done|error
    agents_json = Column(JSON)
    result_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    scene = relationship("Scene", back_populates="jobs")


class Artifact(Base):
    """Artifact model for storing generated patches/diffs."""
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    variant = Column(String, nullable=False)  # safe|bold|red_team
    diff_key = Column(Text)  # S3 key for diff file
    metrics_before = Column(JSON)
    metrics_after = Column(JSON)
    receipts_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    scene = relationship("Scene", back_populates="artifacts")


class SceneEmbedding(Base):
    """Scene embedding model for semantic search."""
    __tablename__ = "scene_embeddings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    chunk_no = Column(Integer, nullable=False)
    content = Column(Text)
    
    # Use vector type if available, otherwise store as JSON
    if VECTOR_AVAILABLE:
        embedding = Column(Vector(384))  # MiniLM embeddings are 384-dimensional
    else:
        embedding = Column(JSON)  # Fallback to JSON storage
    
    meta = Column(JSON if not VECTOR_AVAILABLE else JSONB)
    
    # Relationships
    scene = relationship("Scene", back_populates="embeddings")
    
    __table_args__ = (
        # Composite index for efficient chunk retrieval
        {"postgresql_using": "btree", "mysql_using": "btree"},
    )
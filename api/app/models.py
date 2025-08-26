"""SQLAlchemy ORM models."""
from sqlalchemy import Column, String, Integer, Text, JSON, TIMESTAMP, ForeignKey, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from .db import Base

# Simplified approach without pgvector for now
VECTOR_AVAILABLE = False


class Scene(Base):
    """Scene model representing a chapter/scene in the manuscript."""
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)  # e.g., "ch02_s03"
    chapter = Column(Integer, nullable=False, index=True)
    order_in_chapter = Column(Integer, nullable=False, index=True)
    pov = Column(Text, index=True)
    location = Column(Text, index=True)
    text_path = Column(Text)  # Path to markdown file
    beats_json = Column(JSON)
    links_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), index=True)
    
    # Relationships
    jobs = relationship("Job", back_populates="scene", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="scene", cascade="all, delete-orphan")
    embeddings = relationship("SceneEmbedding", back_populates="scene", cascade="all, delete-orphan")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_scene_chapter_order', 'chapter', 'order_in_chapter'),
        Index('idx_scene_pov_location', 'pov', 'location'),
        Index('idx_scene_created_updated', 'created_at', 'updated_at'),
    )


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
    status = Column(String, nullable=False, default="queued", index=True)  # queued|running|done|error
    job_type = Column(String, nullable=False, default="agent_processing", index=True)
    agents_json = Column(JSON)
    result_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), index=True)
    
    # Relationships
    scene = relationship("Scene", back_populates="jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_job_scene_status', 'scene_id', 'status'),
        Index('idx_job_status_type', 'status', 'job_type'),
        Index('idx_job_created_status', 'created_at', 'status'),
    )


class Artifact(Base):
    """Artifact model for storing generated patches/diffs."""
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    artifact_type = Column(String, nullable=False, index=True)  # agent_result|patch|diff
    variant = Column(String, nullable=False, index=True)  # safe|bold|red_team
    content = Column(Text)  # Direct content storage
    meta_data = Column(JSON)  # Additional metadata (renamed from metadata)
    diff_key = Column(Text)  # S3 key for diff file (optional)
    metrics_before = Column(JSON)
    metrics_after = Column(JSON)
    receipts_json = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="artifacts")
    scene = relationship("Scene", back_populates="artifacts")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_artifact_job_type', 'job_id', 'artifact_type'),
        Index('idx_artifact_scene_variant', 'scene_id', 'variant'),
        Index('idx_artifact_type_created', 'artifact_type', 'created_at'),
    )


class SceneEmbedding(Base):
    """Scene embedding model for semantic search."""
    __tablename__ = "scene_embeddings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    chunk_no = Column(Integer, nullable=False)
    content = Column(Text)
    
    # Store embeddings as JSON array
    embedding = Column(JSON)  # JSON storage for embeddings
    
    meta = Column(JSON)
    
    # Relationships
    scene = relationship("Scene", back_populates="embeddings")
    
    __table_args__ = (
        # Composite index for efficient chunk retrieval
        {"postgresql_using": "btree", "mysql_using": "btree"},
    )
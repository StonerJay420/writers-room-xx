"""Job model for agent processing tasks."""
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from . import Base


class Job(Base):
    """Job model for tracking agent processing."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="queued")  # queued|running|done|error
    agents_json = Column(String)  # JSON as string  
    result_json = Column(String)  # JSON as string
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    scene = relationship("Scene", back_populates="jobs")
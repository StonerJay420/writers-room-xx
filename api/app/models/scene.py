"""Scene model for manuscript scenes."""
from sqlalchemy import Column, String, Integer, Text, JSON, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from . import Base


class Scene(Base):
    """Scene model representing a chapter/scene in the manuscript."""
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)  # e.g., "ch02_s03"
    chapter = Column(Integer, nullable=False, index=True)
    order_in_chapter = Column(Integer, nullable=False)
    pov = Column(String)
    location = Column(String)
    text_path = Column(String)  # Path to markdown file
    beats_json = Column(String)  # JSON as string
    links_json = Column(String)  # JSON as string
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="scene", cascade="all, delete-orphan")
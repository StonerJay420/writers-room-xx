"""Character model for manuscript characters."""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func

from . import Base


class Character(Base):
    """Character model for tracking character information."""
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)  # e.g., "char:MC"
    name = Column(String, nullable=False)
    voice_tags_json = Column(String)      # JSON as string
    preferred_words_json = Column(String)  # JSON as string
    banned_words_json = Column(String)     # JSON as string
    arc_flags_json = Column(String)        # JSON as string
    canon_quotes_json = Column(String)     # JSON as string
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
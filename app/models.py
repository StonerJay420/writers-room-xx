from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, List, Optional

Base = declarative_base()

class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)  # e.g., "ch02_s03"
    chapter = Column(Integer)
    order_in_chapter = Column(Integer)
    pov = Column(String)
    location = Column(String)
    text_path = Column(String)  # path to markdown file
    content = Column(Text)  # actual text content
    beats_json = Column(JSON)  # story beats
    links_json = Column(JSON)  # character/location links
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)  # e.g., "char:MC"
    name = Column(String)
    voice_tags_json = Column(JSON)  # ["dry", "observant"]
    preferred_words_json = Column(JSON)  # ["static", "slag", "hiss"]
    banned_words_json = Column(JSON)  # ["neon", "echoes"]
    arc_flags_json = Column(JSON)  # ["trust-issues↑"]
    canon_quotes_json = Column(JSON)  # ["ch01_s01@L13-20"]
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)  # UUID
    scene_id = Column(String)
    status = Column(String)  # queued|running|done|error
    agents_json = Column(JSON)  # list of agents used
    result_json = Column(JSON)  # job results
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Patch(Base):
    __tablename__ = "patches"
    
    id = Column(String, primary_key=True)  # UUID
    scene_id = Column(String)
    variant = Column(String)  # safe|bold|red_team
    diff_content = Column(Text)  # unified diff
    metrics_before = Column(JSON)
    metrics_after = Column(JSON)
    canon_receipts = Column(JSON)  # lore citations
    rationale = Column(Text)  # AI explanation
    created_at = Column(DateTime, default=func.now())

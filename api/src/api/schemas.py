"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base schemas
class SceneBase(BaseModel):
    """Base schema for Scene."""
    chapter: int
    order_in_chapter: int
    pov: Optional[str] = None
    location: Optional[str] = None
    beats_json: Optional[Dict[str, Any]] = None
    links_json: Optional[Dict[str, Any]] = None


class CharacterBase(BaseModel):
    """Base schema for Character."""
    name: str
    voice_tags_json: Optional[Dict[str, Any]] = None
    preferred_words_json: Optional[List[str]] = None
    banned_words_json: Optional[List[str]] = None
    arc_flags_json: Optional[Dict[str, Any]] = None
    canon_quotes_json: Optional[List[str]] = None


class JobBase(BaseModel):
    """Base schema for Job."""
    scene_id: str
    status: str = Field(default="queued", pattern="^(queued|running|done|error)$")
    agents_json: Optional[Dict[str, Any]] = None
    result_json: Optional[Dict[str, Any]] = None


class ArtifactBase(BaseModel):
    """Base schema for Artifact."""
    scene_id: str
    variant: str = Field(pattern="^(safe|bold|red_team)$")
    diff_key: Optional[str] = None
    metrics_before: Optional[Dict[str, Any]] = None
    metrics_after: Optional[Dict[str, Any]] = None
    receipts_json: Optional[Dict[str, Any]] = None


# Response schemas will be added as needed for specific endpoints
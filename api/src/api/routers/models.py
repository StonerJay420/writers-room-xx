"""Models router for managing OpenRouter model selection."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from ..config import settings
from ..db import get_write_session, get_read_session


router = APIRouter(prefix="/models", tags=["models"])


class ModelInfo(BaseModel):
    """Model information from OpenRouter."""
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, float]] = None
    
    
class AgentModelConfig(BaseModel):
    """Configuration for agent model selection."""
    agent_name: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 2000


class AgentModelPreference(BaseModel):
    """Stored preference for agent models."""
    lore_archivist: str = "anthropic/claude-3-opus"
    grim_editor: str = "openai/gpt-4-turbo-preview"
    tone_metrics: str = "anthropic/claude-3-sonnet"
    supervisor: str = "anthropic/claude-3-opus"


# In-memory storage for model preferences (could be moved to DB)
model_preferences = AgentModelPreference()


@router.get("/available", response_model=List[ModelInfo])
async def get_available_models():
    """Fetch list of available models from OpenRouter."""
    try:
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.openrouter_base_url}/models",
                headers=headers
            )
            
            if response.status_code != 200:
                # Fallback to commonly available models
                return get_fallback_models()
            
            data = response.json()
            models = []
            
            for model_data in data.get("data", []):
                # Extract pricing info
                pricing = {}
                if "pricing" in model_data:
                    pricing = {
                        "prompt": float(model_data["pricing"].get("prompt", 0)),
                        "completion": float(model_data["pricing"].get("completion", 0))
                    }
                
                models.append(ModelInfo(
                    id=model_data["id"],
                    name=model_data.get("name", model_data["id"]),
                    description=model_data.get("description"),
                    context_length=model_data.get("context_length"),
                    pricing=pricing
                ))
            
            # Sort by name for better UX
            models.sort(key=lambda x: x.name)
            return models
            
    except Exception as e:
        print(f"Error fetching models: {e}")
        return get_fallback_models()


def get_fallback_models() -> List[ModelInfo]:
    """Return a fallback list of commonly available models."""
    return [
        ModelInfo(
            id="openai/gpt-4-turbo-preview",
            name="GPT-4 Turbo",
            description="OpenAI's most capable model",
            context_length=128000,
            pricing={"prompt": 0.01, "completion": 0.03}
        ),
        ModelInfo(
            id="openai/gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            description="Fast and efficient",
            context_length=16385,
            pricing={"prompt": 0.0005, "completion": 0.0015}
        ),
        ModelInfo(
            id="anthropic/claude-3-opus",
            name="Claude 3 Opus",
            description="Most capable Claude model",
            context_length=200000,
            pricing={"prompt": 0.015, "completion": 0.075}
        ),
        ModelInfo(
            id="anthropic/claude-3-sonnet",
            name="Claude 3 Sonnet",
            description="Balanced performance",
            context_length=200000,
            pricing={"prompt": 0.003, "completion": 0.015}
        ),
        ModelInfo(
            id="anthropic/claude-3-haiku",
            name="Claude 3 Haiku",
            description="Fast and affordable",
            context_length=200000,
            pricing={"prompt": 0.00025, "completion": 0.00125}
        ),
        ModelInfo(
            id="google/gemini-pro",
            name="Gemini Pro",
            description="Google's advanced model",
            context_length=32768,
            pricing={"prompt": 0.000125, "completion": 0.000375}
        ),
        ModelInfo(
            id="meta-llama/llama-3-70b-instruct",
            name="Llama 3 70B",
            description="Open source powerhouse",
            context_length=8192,
            pricing={"prompt": 0.0008, "completion": 0.0008}
        ),
        ModelInfo(
            id="mistralai/mixtral-8x7b-instruct",
            name="Mixtral 8x7B",
            description="Efficient mixture of experts",
            context_length=32768,
            pricing={"prompt": 0.0006, "completion": 0.0006}
        )
    ]


@router.get("/preferences", response_model=AgentModelPreference)
async def get_model_preferences():
    """Get current model preferences for all agents."""
    return model_preferences


@router.post("/preferences")
async def update_model_preferences(preferences: AgentModelPreference):
    """Update model preferences for agents."""
    global model_preferences
    model_preferences = preferences
    return {"status": "updated", "preferences": preferences}


@router.post("/agent-config")
async def set_agent_model(config: AgentModelConfig):
    """Set model for a specific agent."""
    global model_preferences
    
    if config.agent_name == "lore_archivist":
        model_preferences.lore_archivist = config.model_id
    elif config.agent_name == "grim_editor":
        model_preferences.grim_editor = config.model_id
    elif config.agent_name == "tone_metrics":
        model_preferences.tone_metrics = config.model_id
    elif config.agent_name == "supervisor":
        model_preferences.supervisor = config.model_id
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {config.agent_name}")
    
    return {"status": "updated", "agent": config.agent_name, "model": config.model_id}
"""Models and agent configuration router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import json
from pathlib import Path

router = APIRouter(prefix="/models", tags=["models"])


class AgentConfigRequest(BaseModel):
    agent_name: str
    model_id: str


class ModelPreferences(BaseModel):
    lore_archivist: str = "anthropic/claude-3-opus"
    grim_editor: str = "openai/gpt-4-turbo-preview"
    tone_metrics: str = "anthropic/claude-3-sonnet"
    supervisor: str = "anthropic/claude-3-opus"


# Available models for each provider
AVAILABLE_MODELS = {
    "anthropic/claude-3-opus": "Claude 3 Opus",
    "anthropic/claude-3-sonnet": "Claude 3 Sonnet",
    "anthropic/claude-3-haiku": "Claude 3 Haiku",
    "openai/gpt-4-turbo-preview": "GPT-4 Turbo Preview",
    "openai/gpt-4": "GPT-4",
    "openai/gpt-3.5-turbo": "GPT-3.5 Turbo",
    "google/gemini-pro": "Gemini Pro",
    "meta-llama/llama-2-70b-chat": "Llama 2 70B Chat",
    "mistralai/mistral-7b-instruct": "Mistral 7B Instruct"
}

# Default preferences
_model_preferences = ModelPreferences()


@router.get("/list")
async def list_models() -> Dict[str, str]:
    """Get list of available models."""
    return AVAILABLE_MODELS


@router.get("/preferences")
async def get_model_preferences() -> ModelPreferences:
    """Get current model preferences for agents."""
    return _model_preferences


@router.post("/agent-config")
async def update_agent_config(config: AgentConfigRequest) -> Dict[str, str]:
    """Update model configuration for a specific agent."""
    global _model_preferences
    
    # Validate model exists
    if config.model_id not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Model {config.model_id} not available"
        )
    
    # Validate agent name
    valid_agents = ["lore_archivist", "grim_editor", "tone_metrics", "supervisor"]
    if config.agent_name not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name. Must be one of: {valid_agents}"
        )
    
    # Update preferences
    setattr(_model_preferences, config.agent_name, config.model_id)
    
    return {
        "status": "success",
        "agent": config.agent_name,
        "model": config.model_id
    }

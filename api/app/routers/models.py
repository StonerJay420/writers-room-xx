"""Models and agent configuration router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import json
from pathlib import Path

router = APIRouter(prefix="/models", tags=["models"])


class AgentConfigRequest(BaseModel):
    agent_name: str
    llm_model_id: str


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


@router.get("/available")
async def get_available_models() -> Dict[str, List[str]]:
    """Get all available models grouped by provider."""
    return {
        "anthropic": [
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku"
        ],
        "openai": [
            "openai/gpt-4-turbo-preview",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo"
        ],
        "meta": [
            "meta-llama/llama-2-70b-chat",
            "meta-llama/llama-2-13b-chat"
        ]
    }


@router.get("/preferences")
async def get_model_preferences() -> Dict[str, str]:
    """Get current model preferences for all agents."""
    return {
        "lore_archivist": "anthropic/claude-3-opus",
        "grim_editor": "openai/gpt-4-turbo-preview",
        "tone_metrics": "anthropic/claude-3-sonnet",
        "supervisor": "anthropic/claude-3-opus"
    }


@router.post("/agent-config")
async def update_agent_model(request: Dict[str, str]) -> Dict[str, str]:
    """Update model configuration for a specific agent."""
    agent_name = request.get("agent_name")
    model_id = request.get("llm_model_id")

    if not agent_name or not model_id:
        raise HTTPException(status_code=400, detail="Missing agent_name or llm_model_id")

    # In a real implementation, you'd save this to a config store
    return {"status": "success", "agent": agent_name, "model": model_id}
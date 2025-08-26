"""Models and agent configuration router."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
import httpx
import os
from pathlib import Path

router = APIRouter(prefix="/models", tags=["models"])


class AgentConfigRequest(BaseModel):
    agent_name: str
    llm_model_id: str


class ModelInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    context_length: Optional[int] = None
    pricing: Optional[Dict[str, float]] = None
    provider: str
    modalities: List[str] = ["text"]


class ModelPreferences(BaseModel):
    lore_archivist: str = "anthropic/claude-sonnet-4-20250514"
    grim_editor: str = "openai/gpt-5"
    tone_metrics: str = "anthropic/claude-sonnet-4-20250514"
    supervisor: str = "anthropic/claude-sonnet-4-20250514"


# Comprehensive model catalog with real provider information
ANTHROPIC_MODELS = [
    ModelInfo(
        id="anthropic/claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        description="Latest Claude model with enhanced reasoning and capabilities",
        context_length=200000,
        pricing={"prompt": 0.003, "completion": 0.015},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-7-sonnet-20250219",
        name="Claude 3.7 Sonnet",
        description="Enhanced Claude 3.5 with improved reasoning",
        context_length=200000,
        pricing={"prompt": 0.003, "completion": 0.015},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet (Oct 2024)",
        description="Claude 3.5 Sonnet with computer use capabilities",
        context_length=200000,
        pricing={"prompt": 0.003, "completion": 0.015},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        description="Fast, cost-effective model for everyday tasks",
        context_length=200000,
        pricing={"prompt": 0.0008, "completion": 0.004},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-opus-20240229",
        name="Claude 3 Opus",
        description="Most powerful Claude 3 model for complex tasks",
        context_length=200000,
        pricing={"prompt": 0.015, "completion": 0.075},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-sonnet-20240229",
        name="Claude 3 Sonnet",
        description="Balanced Claude 3 model for most tasks",
        context_length=200000,
        pricing={"prompt": 0.003, "completion": 0.015},
        provider="anthropic",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="anthropic/claude-3-haiku-20240307",
        name="Claude 3 Haiku",
        description="Fast and affordable Claude 3 model",
        context_length=200000,
        pricing={"prompt": 0.00025, "completion": 0.00125},
        provider="anthropic",
        modalities=["text", "image"]
    )
]

OPENAI_MODELS = [
    ModelInfo(
        id="openai/gpt-5",
        name="GPT-5",
        description="Latest OpenAI model released August 2025 with enhanced capabilities",
        context_length=128000,
        pricing={"prompt": 0.01, "completion": 0.03},
        provider="openai",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="openai/gpt-4o",
        name="GPT-4o",
        description="GPT-4 Omni with multimodal capabilities",
        context_length=128000,
        pricing={"prompt": 0.005, "completion": 0.015},
        provider="openai",
        modalities=["text", "image", "audio"]
    ),
    ModelInfo(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        description="Affordable and intelligent small model",
        context_length=128000,
        pricing={"prompt": 0.00015, "completion": 0.0006},
        provider="openai",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="openai/gpt-4-turbo",
        name="GPT-4 Turbo",
        description="High-intelligence model for complex, multi-step tasks",
        context_length=128000,
        pricing={"prompt": 0.01, "completion": 0.03},
        provider="openai",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="openai/gpt-4",
        name="GPT-4",
        description="Previous generation high-intelligence model",
        context_length=8192,
        pricing={"prompt": 0.03, "completion": 0.06},
        provider="openai",
        modalities=["text"]
    ),
    ModelInfo(
        id="openai/gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        description="Fast, affordable model for simple tasks",
        context_length=16385,
        pricing={"prompt": 0.0005, "completion": 0.0015},
        provider="openai",
        modalities=["text"]
    )
]

GOOGLE_MODELS = [
    ModelInfo(
        id="google/gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        description="Latest fast multimodal model from Google",
        context_length=2097152,
        pricing={"prompt": 0.000075, "completion": 0.0003},
        provider="google",
        modalities=["text", "image", "video", "audio"]
    ),
    ModelInfo(
        id="google/gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        description="Advanced reasoning with long context",
        context_length=2097152,
        pricing={"prompt": 0.00125, "completion": 0.005},
        provider="google",
        modalities=["text", "image", "video", "audio"]
    ),
    ModelInfo(
        id="google/gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        description="Mid-size multimodal model for complex reasoning",
        context_length=2097152,
        pricing={"prompt": 0.00125, "completion": 0.005},
        provider="google",
        modalities=["text", "image", "video", "audio"]
    ),
    ModelInfo(
        id="google/gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        description="Fast and versatile multimodal model",
        context_length=1048576,
        pricing={"prompt": 0.000075, "completion": 0.0003},
        provider="google",
        modalities=["text", "image", "video", "audio"]
    ),
    ModelInfo(
        id="google/gemini-pro",
        name="Gemini Pro",
        description="Original Gemini Pro model",
        context_length=32768,
        pricing={"prompt": 0.0005, "completion": 0.0015},
        provider="google",
        modalities=["text"]
    )
]

XAI_MODELS = [
    ModelInfo(
        id="xai/grok-2-vision-1212",
        name="Grok-2 Vision",
        description="Latest Grok model with vision capabilities",
        context_length=8192,
        pricing={"prompt": 0.002, "completion": 0.01},
        provider="xai",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="xai/grok-2-1212",
        name="Grok-2",
        description="Large context Grok model for complex tasks",
        context_length=131072,
        pricing={"prompt": 0.002, "completion": 0.01},
        provider="xai",
        modalities=["text"]
    ),
    ModelInfo(
        id="xai/grok-vision-beta",
        name="Grok Vision Beta",
        description="Beta version with multimodal capabilities",
        context_length=8192,
        pricing={"prompt": 0.002, "completion": 0.01},
        provider="xai",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="xai/grok-beta",
        name="Grok Beta",
        description="Beta version of Grok language model",
        context_length=131072,
        pricing={"prompt": 0.002, "completion": 0.01},
        provider="xai",
        modalities=["text"]
    )
]

META_MODELS = [
    ModelInfo(
        id="meta-llama/llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct",
        description="Latest instruction-tuned Llama model",
        context_length=131072,
        pricing={"prompt": 0.0008, "completion": 0.0008},
        provider="meta",
        modalities=["text"]
    ),
    ModelInfo(
        id="meta-llama/llama-3.2-11b-vision-instruct",
        name="Llama 3.2 11B Vision Instruct",
        description="Multimodal Llama with vision capabilities",
        context_length=131072,
        pricing={"prompt": 0.00018, "completion": 0.00018},
        provider="meta",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="meta-llama/llama-3.2-90b-vision-instruct",
        name="Llama 3.2 90B Vision Instruct",
        description="Large multimodal Llama model",
        context_length=131072,
        pricing={"prompt": 0.0009, "completion": 0.0009},
        provider="meta",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="meta-llama/llama-3.1-405b-instruct",
        name="Llama 3.1 405B Instruct",
        description="Largest open-weight language model",
        context_length=131072,
        pricing={"prompt": 0.005, "completion": 0.005},
        provider="meta",
        modalities=["text"]
    ),
    ModelInfo(
        id="meta-llama/llama-3.1-70b-instruct",
        name="Llama 3.1 70B Instruct",
        description="High-performance open-weight model",
        context_length=131072,
        pricing={"prompt": 0.0008, "completion": 0.0008},
        provider="meta",
        modalities=["text"]
    ),
    ModelInfo(
        id="meta-llama/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        description="Efficient open-weight model",
        context_length=131072,
        pricing={"prompt": 0.00018, "completion": 0.00018},
        provider="meta",
        modalities=["text"]
    )
]

MISTRAL_MODELS = [
    ModelInfo(
        id="mistralai/mistral-large-2411",
        name="Mistral Large (Nov 2024)",
        description="Latest flagship model from Mistral",
        context_length=128000,
        pricing={"prompt": 0.002, "completion": 0.006},
        provider="mistral",
        modalities=["text"]
    ),
    ModelInfo(
        id="mistralai/pixtral-12b-2409",
        name="Pixtral 12B",
        description="Multimodal model with vision capabilities",
        context_length=128000,
        pricing={"prompt": 0.00015, "completion": 0.00015},
        provider="mistral",
        modalities=["text", "image"]
    ),
    ModelInfo(
        id="mistralai/mistral-small-2409",
        name="Mistral Small",
        description="Cost-effective model for simple tasks",
        context_length=128000,
        pricing={"prompt": 0.0002, "completion": 0.0006},
        provider="mistral",
        modalities=["text"]
    ),
    ModelInfo(
        id="mistralai/mistral-nemo-2407",
        name="Mistral Nemo",
        description="12B parameter model for efficiency",
        context_length=128000,
        pricing={"prompt": 0.00015, "completion": 0.00015},
        provider="mistral",
        modalities=["text"]
    )
]

# Combine all models
ALL_MODELS = ANTHROPIC_MODELS + OPENAI_MODELS + GOOGLE_MODELS + XAI_MODELS + META_MODELS + MISTRAL_MODELS

# Default preferences with latest models
_model_preferences = ModelPreferences()


@router.get("/available")
async def get_available_models() -> List[ModelInfo]:
    """Get all available models with detailed information."""
    return ALL_MODELS


@router.get("/preferences")
async def get_model_preferences() -> Dict[str, str]:
    """Get current model preferences for all agents."""
    return {
        "lore_archivist": _model_preferences.lore_archivist,
        "grim_editor": _model_preferences.grim_editor,
        "tone_metrics": _model_preferences.tone_metrics,
        "supervisor": _model_preferences.supervisor
    }


@router.post("/agent-config")
async def update_agent_model(request: Dict[str, str]) -> Dict[str, str]:
    """Update model configuration for a specific agent."""
    agent_name = request.get("agent_name")
    model_id = request.get("llm_model_id")

    if not agent_name or not model_id:
        raise HTTPException(status_code=400, detail="Missing agent_name or llm_model_id")

    # Validate model exists
    valid_models = [model.id for model in ALL_MODELS]
    if model_id not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model_id: {model_id}")

    # Validate agent name
    if agent_name not in ["lore_archivist", "grim_editor", "tone_metrics", "supervisor"]:
        raise HTTPException(status_code=400, detail=f"Invalid agent_name: {agent_name}")

    # Update global preferences
    global _model_preferences
    setattr(_model_preferences, agent_name, model_id)

    return {"status": "success", "agent": agent_name, "model": model_id}


@router.get("/providers")
async def get_providers() -> Dict[str, List[ModelInfo]]:
    """Get models grouped by provider."""
    providers = {}
    for model in ALL_MODELS:
        if model.provider not in providers:
            providers[model.provider] = []
        providers[model.provider].append(model)
    return providers


@router.get("/validate/{model_id}")
async def validate_model(model_id: str) -> Dict[str, bool]:
    """Validate if a model ID is available."""
    valid_models = [model.id for model in ALL_MODELS]
    return {"valid": model_id in valid_models}
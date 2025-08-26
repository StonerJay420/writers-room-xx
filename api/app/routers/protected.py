"""Protected endpoints that require authentication."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ..auth import get_current_user, require_rate_limit, get_user_llm_client
from ..services.llm_client import LLMClient

router = APIRouter(prefix="/protected", tags=["protected"])
logger = logging.getLogger(__name__)


class LLMTestRequest(BaseModel):
    """Request to test LLM functionality."""
    message: str = "Hello, this is a test message"
    model: str = "anthropic/claude-3-haiku"


class LLMTestResponse(BaseModel):
    """Response from LLM test."""
    success: bool
    response: Optional[str] = None
    model: str
    usage: Optional[Dict[str, Any]] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    """User information response."""
    name: str
    created_at: str
    usage_count: int
    rate_limit_remaining: int
    has_llm_key: bool


@router.get("/user", response_model=UserInfoResponse)
async def get_user_info(user: dict = Depends(get_current_user)):
    """
    Get current user information.
    
    Shows session details and usage statistics.
    """
    # Calculate remaining rate limit
    rate_info = user["rate_limit"]
    remaining = max(0, 60 - rate_info["requests"])
    
    return UserInfoResponse(
        name=user["name"],
        created_at=user["created_at"].isoformat(),
        usage_count=user["usage_count"],
        rate_limit_remaining=remaining,
        has_llm_key=user.get("key_hash") is not None
    )


@router.post("/test-llm", response_model=LLMTestResponse)
async def test_llm(
    request: LLMTestRequest,
    user: dict = Depends(require_rate_limit(limit=10, window=60)),
    llm_client: LLMClient = Depends(get_user_llm_client)
):
    """
    Test LLM functionality with user's API key.
    
    This endpoint allows users to verify their OpenRouter API key
    is working correctly and check model availability.
    """
    try:
        if not llm_client.api_key:
            return LLMTestResponse(
                success=False,
                response=None,
                model=request.model,
                error="No OpenRouter API key configured. Please add your key via /api/auth/llm-key"
            )
        
        # Make test call to LLM
        messages = [{"role": "user", "content": request.message}]
        
        response = await llm_client.complete(
            messages=messages,
            model=request.model,
            temperature=0.7,
            max_tokens=100
        )
        
        logger.info(f"LLM test successful for user {user['name']}")
        
        return LLMTestResponse(
            success=True,
            response=response.content,
            model=response.model,
            usage=response.usage,
            cost_usd=response.cost_usd
        )
        
    except Exception as e:
        logger.error(f"LLM test failed for user {user['name']}: {e}")
        return LLMTestResponse(
            success=False,
            response=None,
            model=request.model,
            error=str(e)
        )


@router.get("/available-models")
async def get_available_models(user: dict = Depends(get_current_user)):
    """
    Get list of available models for the user.
    
    Returns models that can be used with the user's API key.
    """
    return {
        "models": [
            {
                "id": "anthropic/claude-3-opus",
                "name": "Claude 3 Opus",
                "description": "Most capable Claude model for complex tasks",
                "cost_per_1k": 0.015,
                "alias": "reasoner-1"
            },
            {
                "id": "anthropic/claude-3-sonnet",
                "name": "Claude 3 Sonnet", 
                "description": "Balanced Claude model for most tasks",
                "cost_per_1k": 0.003,
                "alias": "stylist-1"
            },
            {
                "id": "anthropic/claude-3-haiku",
                "name": "Claude 3 Haiku",
                "description": "Fastest Claude model for simple tasks",
                "cost_per_1k": 0.00025,
                "alias": "critic-1"
            },
            {
                "id": "openai/gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "description": "Latest GPT-4 model with improved capabilities",
                "cost_per_1k": 0.01
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and efficient model for most tasks",
                "cost_per_1k": 0.001
            }
        ],
        "recommended": {
            "editing": "anthropic/claude-3-sonnet",
            "analysis": "anthropic/claude-3-opus", 
            "quick_tasks": "anthropic/claude-3-haiku"
        }
    }
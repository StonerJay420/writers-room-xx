"""Authentication and API key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

from ..auth import AuthManager, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    """Request to create new user session."""
    name: Optional[str] = Field(default="default", description="Session name")


class SessionResponse(BaseModel):
    """Response with session info."""
    api_key: str = Field(description="API key for authentication")
    message: str = Field(description="Success message")
    instructions: str = Field(description="How to use the API key")


class LLMKeyRequest(BaseModel):
    """Request to store LLM API key."""
    openrouter_api_key: str = Field(description="OpenRouter API key", min_length=20)


class LLMKeyResponse(BaseModel):
    """Response for LLM key operations."""
    message: str = Field(description="Operation result")
    has_key: bool = Field(description="Whether user has LLM key stored")


class StatusResponse(BaseModel):
    """User status response."""
    name: str = Field(description="Session name")
    created_at: str = Field(description="Session creation time")
    usage_count: int = Field(description="Total API calls made")
    has_llm_key: bool = Field(description="Whether LLM key is configured")
    llm_status: str = Field(description="LLM availability status")


@router.post("/session", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """
    Create a new user session with API key.
    
    This is the entry point for new users to get started with Writers Room X.
    The API key should be used in subsequent requests for authentication.
    """
    try:
        api_key = AuthManager.create_user_session(request.name)
        
        return SessionResponse(
            api_key=api_key,
            message="Session created successfully",
            instructions="Use this API key in the Authorization header: 'Bearer <api_key>' or X-API-Key header"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.post("/llm-key", response_model=LLMKeyResponse)
async def store_llm_key(
    request: LLMKeyRequest,
    user: dict = Depends(get_current_user)
):
    """
    Store user's OpenRouter API key for LLM access.
    
    This implements BYOK (Bring Your Own Key) - users provide their own
    OpenRouter API key which is stored securely and used for all LLM calls.
    """
    try:
        # Validate the key format (basic check)
        if not request.openrouter_api_key.startswith(("sk-", "or-")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OpenRouter API key format"
            )
        
        AuthManager.store_user_llm_key(user["key_hash"], request.openrouter_api_key)
        
        return LLMKeyResponse(
            message="OpenRouter API key stored successfully",
            has_key=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store LLM key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store API key"
        )


@router.get("/llm-key", response_model=LLMKeyResponse)
async def get_llm_key_status(user: dict = Depends(get_current_user)):
    """
    Check if user has an LLM API key configured.
    
    Returns status but never returns the actual key for security.
    """
    has_key = AuthManager.get_user_llm_key(user["key_hash"]) is not None
    
    return LLMKeyResponse(
        message="LLM key configured" if has_key else "No LLM key configured",
        has_key=has_key
    )


@router.delete("/llm-key", response_model=LLMKeyResponse)
async def remove_llm_key(user: dict = Depends(get_current_user)):
    """
    Remove user's stored LLM API key.
    
    This will disable LLM features until a new key is provided.
    """
    try:
        removed = AuthManager.remove_user_llm_key(user["key_hash"])
        
        return LLMKeyResponse(
            message="LLM key removed successfully" if removed else "No LLM key to remove",
            has_key=False
        )
    except Exception as e:
        logger.error(f"Failed to remove LLM key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove API key"
        )


@router.get("/status", response_model=StatusResponse)
async def get_user_status(user: dict = Depends(get_current_user)):
    """
    Get current user status and configuration.
    
    Shows session info, usage stats, and LLM availability.
    """
    has_llm_key = AuthManager.get_user_llm_key(user["key_hash"]) is not None
    
    return StatusResponse(
        name=user["name"],
        created_at=user["created_at"].isoformat(),
        usage_count=user["usage_count"],
        has_llm_key=has_llm_key,
        llm_status="enabled" if has_llm_key else "disabled - provide OpenRouter API key"
    )
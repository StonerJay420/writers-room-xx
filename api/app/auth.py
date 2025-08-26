"""Authentication and authorization system."""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Simple in-memory store for demo - would use Redis/DB in production
_api_keys: Dict[str, Dict[str, Any]] = {}
_user_llm_keys: Dict[str, str] = {}  # user_id -> encrypted_llm_key

security = HTTPBearer(auto_error=False)


class AuthManager:
    """Manages API authentication and user LLM keys."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key."""
        return f"wrx_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    def create_user_session(name: str = "default") -> str:
        """Create a new user session with API key."""
        api_key = AuthManager.generate_api_key()
        key_hash = AuthManager.hash_key(api_key)
        
        _api_keys[key_hash] = {
            "name": name,
            "created_at": datetime.utcnow(),
            "last_used": datetime.utcnow(),
            "usage_count": 0,
            "rate_limit": {"requests": 0, "window_start": datetime.utcnow()}
        }
        
        logger.info(f"Created new user session for: {name}")
        return api_key
    
    @staticmethod
    def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return user info."""
        if not api_key:
            return None
            
        key_hash = AuthManager.hash_key(api_key)
        user_info = _api_keys.get(key_hash)
        
        if user_info:
            # Update last used
            user_info["last_used"] = datetime.utcnow()
            user_info["usage_count"] += 1
            
        return user_info
    
    @staticmethod
    def store_user_llm_key(user_key_hash: str, llm_key: str) -> None:
        """Store user's LLM key securely."""
        # Simple encryption - in production use proper encryption
        encrypted = secrets.token_urlsafe(16) + ":" + llm_key
        _user_llm_keys[user_key_hash] = encrypted
        logger.info(f"Stored LLM key for user: {user_key_hash[:8]}...")
    
    @staticmethod
    def get_user_llm_key(user_key_hash: str) -> Optional[str]:
        """Retrieve user's LLM key."""
        encrypted = _user_llm_keys.get(user_key_hash)
        if encrypted and ":" in encrypted:
            return encrypted.split(":", 1)[1]
        return None
    
    @staticmethod
    def remove_user_llm_key(user_key_hash: str) -> bool:
        """Remove user's LLM key."""
        if user_key_hash in _user_llm_keys:
            del _user_llm_keys[user_key_hash]
            logger.info(f"Removed LLM key for user: {user_key_hash[:8]}...")
            return True
        return False


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user from request."""
    
    # Try Authorization header first
    api_key = None
    if credentials:
        api_key = credentials.credentials
    
    # Fallback to X-API-Key header
    if not api_key:
        api_key = request.headers.get("X-API-Key")
    
    # Fallback to query parameter for development
    if not api_key:
        api_key = request.query_params.get("api_key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Use Authorization: Bearer <key> or X-API-Key header"
        )
    
    user_info = AuthManager.validate_api_key(api_key)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Add the hashed key for LLM key lookup
    user_info["key_hash"] = AuthManager.hash_key(api_key)
    return user_info


def get_user_llm_client(user: Dict[str, Any] = Depends(get_current_user)):
    """Get LLM client with user's API key."""
    from .services.llm_client import LLMClient
    
    user_llm_key = AuthManager.get_user_llm_key(user["key_hash"])
    if not user_llm_key:
        # Return disabled client
        return LLMClient(api_key=None)
    
    return LLMClient(api_key=user_llm_key)


class RateLimiter:
    """Simple rate limiting implementation."""
    
    @staticmethod
    def check_rate_limit(user_info: Dict[str, Any], limit: int = 60, window: int = 60) -> bool:
        """Check if user is within rate limits."""
        now = datetime.utcnow()
        rate_info = user_info["rate_limit"]
        
        # Reset window if needed
        if (now - rate_info["window_start"]).seconds >= window:
            rate_info["requests"] = 0
            rate_info["window_start"] = now
        
        # Check limit
        if rate_info["requests"] >= limit:
            return False
        
        rate_info["requests"] += 1
        return True


def require_rate_limit(limit: int = 60, window: int = 60):
    """Rate limiting dependency factory."""
    def _rate_limit_dependency(user: Dict[str, Any] = Depends(get_current_user)):
        """Rate limiting dependency."""
        if not RateLimiter.check_rate_limit(user, limit, window):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. {limit} requests per {window} seconds allowed.",
                headers={"Retry-After": str(window)}
            )
        return user
    return _rate_limit_dependency
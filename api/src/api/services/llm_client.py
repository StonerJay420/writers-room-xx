"""LLM client service for OpenRouter API calls as specified in Prompt 11."""
import httpx
import json
import os
from typing import Dict, Any, List, Optional
import logging
import asyncio
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API."""
    content: str
    model: str
    usage: Dict[str, int]
    cost_usd: float


class LLMClient:
    """Client for OpenRouter API calls."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LLM client with API key."""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_timeout = 60
        
        if not self.api_key:
            logger.warning("No OPENROUTER_API_KEY found - LLM features will be disabled")
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False,
        timeout: int = 60
    ) -> LLMResponse:
        """
        Call OpenRouter chat completions API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., 'anthropic/claude-3-opus')
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            json_mode: Request JSON response format
            timeout: Request timeout in seconds
            
        Returns:
            LLMResponse with content, usage, and cost
        """
        if not self.api_key:
            return LLMResponse(
                content="LLM disabled - no API key",
                model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost_usd=0.0
            )
        
        # Map model aliases to actual OpenRouter models
        model_map = {
            "reasoner-1": "anthropic/claude-3-opus",
            "stylist-1": "anthropic/claude-3-sonnet",
            "critic-1": "anthropic/claude-3-haiku",
        }
        actual_model = model_map.get(model, model)
        
        # Build request payload
        payload = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://writers-room-x.replit.app",
            "X-Title": "Writers Room X"
        }
        
        # Retry logic with exponential backoff
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract response content
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        
                        # Calculate cost (rough estimates per model)
                        cost_per_1k_tokens = {
                            "anthropic/claude-3-opus": 0.015,
                            "anthropic/claude-3-sonnet": 0.003,
                            "anthropic/claude-3-haiku": 0.00025,
                            "openai/gpt-4-turbo-preview": 0.01,
                            "openai/gpt-4": 0.03,
                            "openai/gpt-3.5-turbo": 0.001
                        }
                        
                        rate = cost_per_1k_tokens.get(actual_model, 0.001)
                        total_tokens = usage.get("total_tokens", 0)
                        cost_usd = (total_tokens / 1000) * rate
                        
                        return LLMResponse(
                            content=content,
                            model=actual_model,
                            usage=usage,
                            cost_usd=cost_usd
                        )
                    
                    elif response.status_code == 429:  # Rate limit
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        error_data = response.json()
                        raise Exception(f"API error {response.status_code}: {error_data}")
                        
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Timeout, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Timeout after {max_retries} attempts")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Error {e}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        # Should never reach here
        raise Exception(f"Failed after {max_retries} attempts")


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def complete(
    messages: List[Dict[str, str]],
    model: str = "anthropic/claude-3-haiku",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    json_mode: bool = False,
    timeout: int = 60
) -> str:
    """
    Convenience function for simple LLM completions.
    
    Returns just the content string or raises exception on error.
    """
    client = get_llm_client()
    response = await client.complete(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
        timeout=timeout
    )
    return response.content
"""OpenRouter LLM client with retries and backoff as specified in Prompt 11."""
import httpx
import json
import time
import random
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
import asyncio


@dataclass
class CompletionResult:
    """Result from LLM completion call."""
    content: str
    model: str
    usage: Dict[str, int]
    cost_usd: float
    raw_response: Dict[str, Any]


class LLMClient:
    """OpenRouter LLM client with retries and backoff."""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Writers Room X"
        }
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False,
        timeout: int = 60,
        max_retries: int = 3
    ) -> Union[CompletionResult, Dict[str, str]]:
        """
        Complete chat messages with retry logic and exponential backoff.
        
        Args:
            messages: List of chat messages
            model: Model identifier (e.g., "openai/gpt-4-turbo-preview")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON response format
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            CompletionResult on success, error dict on failure
        """
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add JSON mode if requested
        if json_mode:
            request_data["response_format"] = {"type": "json_object"}
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=request_data
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract content
                        content = data["choices"][0]["message"]["content"]
                        
                        # Parse JSON if requested
                        if json_mode:
                            try:
                                content = json.loads(content)
                            except json.JSONDecodeError:
                                return {"error": "Response was not valid JSON", "content": content}
                        
                        # Calculate cost
                        usage = data.get("usage", {})
                        cost = self._calculate_cost(model, usage)
                        
                        return CompletionResult(
                            content=content,
                            model=model,
                            usage=usage,
                            cost_usd=cost,
                            raw_response=data
                        )
                    
                    elif response.status_code == 429:
                        # Rate limit - wait longer
                        if attempt < max_retries:
                            wait_time = (2 ** attempt) + random.uniform(0, 1)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return {"error": "Rate limit exceeded", "status_code": 429}
                    
                    else:
                        return {"error": f"HTTP {response.status_code}", "details": response.text}
            
            except httpx.TimeoutException:
                last_error = "Request timeout"
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(wait_time)
                    continue
            
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + random.uniform(0, 0.5) 
                    await asyncio.sleep(wait_time)
                    continue
        
        return {"error": last_error or "Max retries exceeded"}
    
    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage."""
        # OpenRouter pricing (approximate, per 1M tokens)
        pricing = {
            "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
            "anthropic/claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "openai/gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
            "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5}
        }
        
        model_pricing = pricing.get(model, {"input": 5.0, "output": 15.0})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 6)
"""AI service using OpenRouter for agent processing."""
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..config import settings
from ..config_loader import get_agent_config, get_metric_target


class AIService:
    """Service for interacting with OpenRouter AI models."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Writers Room X"
        }
        
    async def call_agent(
        self,
        agent_name: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        scene_text: Optional[str] = None,
        custom_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call a specific AI agent with the given prompt."""
        
        # Get agent configuration
        agent_config = get_agent_config(agent_name)
        if not agent_config:
            # Default configuration
            agent_config = {
                "model": "openai/gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        
        # Use custom model if provided, otherwise check preferences
        if custom_model:
            model = custom_model
        else:
            # Use updated default preferences with latest models
            model_preferences = {
                "lore_archivist": "anthropic/claude-sonnet-4-20250514",
                "grim_editor": "openai/gpt-5",
                "tone_metrics": "anthropic/claude-sonnet-4-20250514",
                "supervisor": "anthropic/claude-sonnet-4-20250514"
            }
            
            # Get model from preferences based on agent name
            model = model_preferences.get(agent_name, "anthropic/claude-sonnet-4-20250514")
        
        # Build the system prompt based on agent type
        system_prompt = self._build_system_prompt(agent_name, context)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if scene_text:
            messages.append({
                "role": "user", 
                "content": f"Scene text to analyze:\n\n{scene_text}\n\n{prompt}"
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        # Make API call
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": agent_config.get("temperature", 0.7),
                        "max_tokens": agent_config.get("max_tokens", 2000)
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "error": f"API error: {response.status_code}",
                        "details": response.text
                    }
                
                data = response.json()
                
                # Track costs
                usage = data.get("usage", {})
                cost = self._calculate_cost(model, usage)
                
                return {
                    "agent": agent_name,
                    "response": data["choices"][0]["message"]["content"],
                    "model": model,
                    "usage": usage,
                    "cost_usd": cost,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "agent": agent_name
            }
    
    def _build_system_prompt(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt based on agent type."""
        
        if agent_name == "lore_archivist":
            return """You are the Lore Archivist, responsible for maintaining consistency with the story's codex.
Your task is to identify any inconsistencies between the scene text and the established lore, characters, and world rules.
Be precise and cite specific conflicts. Focus on:
1. Character behavior and voice consistency
2. World rule violations
3. Timeline/continuity errors
4. Established fact contradictions"""
        
        elif agent_name == "grim_editor":
            metrics_config = context.get("metrics", {}) if context else {}
            return f"""You are the Grim Editor, a line-by-line prose improvement specialist.
Your task is to enhance the prose while maintaining the author's voice and story intent.
Focus on:
1. Sentence rhythm and flow
2. Word choice precision
3. Removing redundancies
4. Strengthening verbs and reducing adverbs
5. Improving dialogue attribution

Target metrics: {json.dumps(metrics_config, indent=2) if metrics_config else 'Use your best judgment'}

Provide specific line edits with clear before/after suggestions."""
        
        elif agent_name == "tone_metrics":
            return """You are the Tone & Metrics Analyst.
Analyze the text for:
1. Readability scores (Flesch Reading Ease, etc.)
2. Emotional tone and pacing
3. Dialogue vs narrative balance
4. Sentence variety
5. Word complexity distribution

Provide specific metrics and suggestions for improvement."""
        
        else:
            return f"You are an AI assistant helping with manuscript editing. Agent role: {agent_name}"
    
    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate cost based on token usage."""
        # Updated pricing for latest models (per 1M tokens)
        pricing = {
            "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-7-sonnet-20250219": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
            "anthropic/claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
            "anthropic/claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "openai/gpt-5": {"input": 10.0, "output": 30.0},
            "openai/gpt-4o": {"input": 5.0, "output": 15.0},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
            "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "openai/gpt-4": {"input": 30.0, "output": 60.0},
            "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "google/gemini-2.5-flash": {"input": 0.075, "output": 0.3},
            "google/gemini-2.5-pro": {"input": 1.25, "output": 5.0},
            "google/gemini-1.5-pro": {"input": 1.25, "output": 5.0},
            "google/gemini-1.5-flash": {"input": 0.075, "output": 0.3},
            "google/gemini-pro": {"input": 0.5, "output": 1.5},
            "xai/grok-2-vision-1212": {"input": 2.0, "output": 10.0},
            "xai/grok-2-1212": {"input": 2.0, "output": 10.0},
            "xai/grok-vision-beta": {"input": 2.0, "output": 10.0},
            "xai/grok-beta": {"input": 2.0, "output": 10.0},
            "meta-llama/llama-3.3-70b-instruct": {"input": 0.8, "output": 0.8},
            "meta-llama/llama-3.2-11b-vision-instruct": {"input": 0.18, "output": 0.18},
            "meta-llama/llama-3.2-90b-vision-instruct": {"input": 0.9, "output": 0.9},
            "meta-llama/llama-3.1-405b-instruct": {"input": 5.0, "output": 5.0},
            "meta-llama/llama-3.1-70b-instruct": {"input": 0.8, "output": 0.8},
            "meta-llama/llama-3.1-8b-instruct": {"input": 0.18, "output": 0.18},
            "mistralai/mistral-large-2411": {"input": 2.0, "output": 6.0},
            "mistralai/pixtral-12b-2409": {"input": 0.15, "output": 0.15},
            "mistralai/mistral-small-2409": {"input": 0.2, "output": 0.6},
            "mistralai/mistral-nemo-2407": {"input": 0.15, "output": 0.15}
        }
        
        model_pricing = pricing.get(model, {"input": 5.0, "output": 15.0})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 6)


# Global AI service instance
ai_service = AIService()
"""Base agent class with JSON schema validation as specified in Prompt 11."""
import json
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, ValidationError
import logging

from ..services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Base agent class for all AI agents."""
    
    def __init__(self, name: str, model: str, tools: Optional[List[str]] = None):
        """
        Initialize agent.
        
        Args:
            name: Agent name/identifier
            model: LLM model to use (e.g., "openai/gpt-4-turbo-preview")
            tools: List of available tools for this agent
        """
        self.name = name
        self.model = model
        self.tools = tools or []
        self.llm_client: Optional[LLMClient] = None
    
    def set_llm_client(self, llm_client: LLMClient) -> None:
        """Set the LLM client for API calls."""
        self.llm_client = llm_client
    
    @abstractmethod
    def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with given task and context.
        
        Args:
            task: Task specification with required parameters
            context: Additional context (scene text, config, etc.)
            
        Returns:
            Agent result dictionary
        """
        pass
    
    def validate_json_schema(self, data: Any, schema_model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Validate data against a Pydantic schema model.
        
        Args:
            data: Data to validate
            schema_model: Pydantic model class for validation
            
        Returns:
            Validation result with 'valid', 'data', and optional 'errors'
        """
        try:
            # If data is string, try to parse as JSON
            if isinstance(data, str):
                data = json.loads(data)
            
            # Validate with Pydantic model
            validated = schema_model.model_validate(data)
            return {
                "valid": True,
                "data": validated.model_dump(),
                "errors": []
            }
        
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "data": None,
                "errors": [f"JSON decode error: {str(e)}"]
            }
        
        except ValidationError as e:
            return {
                "valid": False,
                "data": None,
                "errors": [str(error) for error in e.errors()]
            }
        
        except Exception as e:
            return {
                "valid": False,
                "data": None,
                "errors": [f"Unexpected error: {str(e)}"]
            }
    
    def build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Build messages array for LLM completion."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    async def call_llm(
        self,
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Call LLM with error handling.
        
        Args:
            messages: Messages to send
            temperature: Override temperature
            max_tokens: Override max tokens
            json_mode: Request JSON response format
            
        Returns:
            LLM response or error dict
        """
        if not self.llm_client:
            return {"error": "No LLM client configured"}
        
        try:
            result = await self.llm_client.complete(
                messages=messages,
                model=self.model,
                temperature=temperature or 0.7,
                max_tokens=max_tokens or 2000,
                json_mode=json_mode
            )
            
            if isinstance(result, dict) and "error" in result:
                logger.error(f"LLM error in {self.name}: {result['error']}")
                return result
            
            return {
                "content": result.content,
                "model": result.model,
                "usage": result.usage,
                "cost_usd": result.cost_usd
            }
            
        except Exception as e:
            error_msg = f"Agent {self.name} LLM call failed: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def log_result(self, result: Dict[str, Any]) -> None:
        """Log agent execution result."""
        if "error" in result:
            logger.error(f"Agent {self.name} failed: {result['error']}")
        else:
            logger.info(f"Agent {self.name} completed successfully")
            if "cost_usd" in result:
                logger.info(f"Agent {self.name} cost: ${result['cost_usd']:.6f}")


# Schema models for common agent outputs
class AgentOutput(BaseModel):
    """Base schema for agent outputs."""
    agent_name: str
    success: bool
    error: Optional[str] = None


class DiffOutput(BaseModel):
    """Schema for agents that produce diffs."""
    diff: str
    rationale: List[str]


class FindingsOutput(BaseModel):
    """Schema for agents that produce findings."""
    findings: List[Dict[str, Any]]
    receipts: List[Dict[str, str]]
    diff: str = ""
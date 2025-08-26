"""Tests for agent functionality."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.agents.base import Agent, AgentOutput, DiffOutput, FindingsOutput


class MockAgent(Agent):
    """Mock agent for testing."""
    
    async def run(self, task, context):
        return {
            "agent": self.name,
            "result": "mock result",
            "task_data": task,
            "context_keys": list(context.keys())
        }


class TestBaseAgent:
    """Test base agent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        assert agent.name == "test_agent"
        assert agent.model == "test_model"
        assert agent.tools == []
        assert agent.llm_client is None
        
    def test_agent_with_tools(self):
        """Test agent initialization with tools."""
        tools = ["search", "analyze"]
        agent = MockAgent(name="test_agent", model="test_model", tools=tools)
        
        assert agent.tools == tools
        
    @pytest.mark.asyncio
    async def test_run_with_error_handling(self):
        """Test agent execution with error handling."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        task = {"text": "test text"}
        context = {"setting": "value"}
        
        result = await agent.run_with_error_handling(task, context)
        
        assert result["agent"] == "test_agent"
        assert result["status"] == "success"
        assert "execution_time" in result
        assert "timestamp" in result
        assert result["result"] == "mock result"
        
    @pytest.mark.asyncio
    async def test_run_with_error_handling_invalid_input(self):
        """Test error handling with invalid input."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        # Invalid task (not a dict)
        result = await agent.run_with_error_handling("invalid", {})
        
        assert result["status"] == "invalid_input"
        assert result["error_type"] == "ValueError"
        assert "execution_time" in result
        
    def test_validate_json_schema(self):
        """Test JSON schema validation."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        # Valid data
        valid_data = {
            "agent_name": "test",
            "status": "success",
            "rationale": ["reason1", "reason2"],
            "data": {"key": "value"}
        }
        
        result = agent.validate_json_schema(valid_data, AgentOutput)
        assert result["valid"] is True
        assert result["data"]["agent_name"] == "test"
        
        # Invalid data
        invalid_data = {
            "agent_name": "test",
            "rationale": "not a list",  # Should be a list
            "data": {"key": "value"}
        }
        
        result = agent.validate_json_schema(invalid_data, AgentOutput)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        
    def test_validate_json_schema_string_input(self):
        """Test JSON schema validation with string input."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        # Valid JSON string
        valid_json = '{"agent_name": "test", "status": "success", "rationale": ["reason"], "data": {}}'
        result = agent.validate_json_schema(valid_json, AgentOutput)
        assert result["valid"] is True
        
        # Invalid JSON string
        invalid_json = '{"agent_name": "test", "invalid": true'
        result = agent.validate_json_schema(invalid_json, AgentOutput)
        assert result["valid"] is False
        assert "JSON decode error" in result["errors"][0]
        
    def test_build_messages(self):
        """Test message building for LLM."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        system_prompt = "You are a helpful assistant."
        user_prompt = "Please help me with this task."
        
        messages = agent.build_messages(system_prompt, user_prompt)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == user_prompt
        
    @pytest.mark.asyncio
    async def test_call_llm_no_client(self):
        """Test LLM call when no client is configured."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        messages = [{"role": "user", "content": "test"}]
        result = await agent.call_llm(messages)
        
        assert "error" in result
        assert "No LLM client configured" in result["error"]
        
    @pytest.mark.asyncio
    async def test_call_llm_with_mock_client(self):
        """Test LLM call with mock client."""
        agent = MockAgent(name="test_agent", model="test_model")
        
        # Mock LLM client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_response.model = "test_model"
        mock_response.usage = {"tokens": 100}
        mock_response.cost_usd = 0.01
        
        mock_client.complete = AsyncMock(return_value=mock_response)
        agent.set_llm_client(mock_client)
        
        messages = [{"role": "user", "content": "test"}]
        result = await agent.call_llm(messages)
        
        assert result["content"] == "Test response"
        assert result["model"] == "test_model"
        assert result["usage"]["tokens"] == 100
        assert result["cost_usd"] == 0.01
        
        # Verify client was called correctly
        mock_client.complete.assert_called_once()
        call_args = mock_client.complete.call_args
        assert call_args[1]["messages"] == messages
        assert call_args[1]["model"] == "test_model"


class TestAgentSchemas:
    """Test agent output schemas."""
    
    def test_diff_output_schema(self):
        """Test DiffOutput schema."""
        data = {
            "diff": "- old line\n+ new line",
            "rationale": ["Fixed grammar", "Improved clarity"],
            "confidence": 0.85
        }
        
        diff_output = DiffOutput(**data)
        assert diff_output.diff == data["diff"]
        assert diff_output.rationale == data["rationale"]
        assert diff_output.confidence == data["confidence"]
        
    def test_findings_output_schema(self):
        """Test FindingsOutput schema."""
        data = {
            "findings": [{"type": "inconsistency", "description": "Character name mismatch"}],
            "receipts": [{"source": "chapter1.md", "quote": "John said hello"}],
            "severity": "warning",
            "recommendations": ["Check character names consistently"]
        }
        
        findings_output = FindingsOutput(**data)
        assert findings_output.findings == data["findings"]
        assert findings_output.receipts == data["receipts"]
        assert findings_output.severity == data["severity"]
        assert findings_output.recommendations == data["recommendations"]
        
    def test_agent_output_schema(self):
        """Test AgentOutput schema."""
        data = {
            "agent_name": "test_agent",
            "status": "success",
            "rationale": ["Analysis completed"],
            "data": {"result": "success"}
        }
        
        agent_output = AgentOutput(**data)
        assert agent_output.agent_name == data["agent_name"]
        assert agent_output.status == data["status"]
        assert agent_output.rationale == data["rationale"]
        assert agent_output.data == data["data"]
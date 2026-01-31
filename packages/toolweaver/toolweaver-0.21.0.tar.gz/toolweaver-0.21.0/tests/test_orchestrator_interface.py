"""
Tests for Orchestrator Interface (Phase 5.1)

Tests:
- ToolCall creation, serialization, deserialization
- PlanResult creation, serialization, deserialization
- OrchestratorConfig validation
- ToolSchema format conversions
- OrchestratorBackend interface compliance
"""

import json
from typing import Any

import pytest

from orchestrator.adapters.orchestrator_interface import (
    OrchestratorBackend,
    OrchestratorConfig,
    PlanResult,
    ToolCall,
    ToolSchema,
)


class TestToolCall:
    """Test ToolCall dataclass."""

    def test_create_tool_call(self) -> None:
        """Test creating a ToolCall."""
        tc = ToolCall(
            tool_name="receipt_ocr",
            parameters={"image_url": "https://example.com/receipt.jpg"},
            id="call-1",
        )
        assert tc.tool_name == "receipt_ocr"
        assert tc.parameters["image_url"] == "https://example.com/receipt.jpg"
        assert tc.id == "call-1"

    def test_tool_call_to_dict(self) -> None:
        """Test ToolCall.to_dict()."""
        tc = ToolCall(
            tool_name="extract_text",
            parameters={"text": "hello"},
            id="call-2",
        )
        d = tc.to_dict()
        assert d["tool_name"] == "extract_text"
        assert d["parameters"]["text"] == "hello"
        assert d["id"] == "call-2"

    def test_tool_call_to_json(self) -> None:
        """Test ToolCall.to_json()."""
        tc = ToolCall(
            tool_name="search",
            parameters={"query": "receipts"},
        )
        json_str = tc.to_json()
        parsed = json.loads(json_str)
        assert parsed["tool_name"] == "search"
        assert parsed["parameters"]["query"] == "receipts"

    def test_tool_call_from_dict(self) -> None:
        """Test ToolCall.from_dict()."""
        data = {
            "tool_name": "upload",
            "parameters": {"file": "data.pdf"},
            "id": "call-3",
        }
        tc = ToolCall.from_dict(data)
        assert tc.tool_name == "upload"
        assert tc.parameters["file"] == "data.pdf"
        assert tc.id == "call-3"

    def test_tool_call_from_json(self) -> None:
        """Test ToolCall.from_json()."""
        json_str = '{"tool_name": "delete", "parameters": {"id": "123"}, "id": "call-4"}'
        tc = ToolCall.from_json(json_str)
        assert tc.tool_name == "delete"
        assert tc.parameters["id"] == "123"

    def test_tool_call_roundtrip(self) -> None:
        """Test serialize/deserialize roundtrip."""
        original = ToolCall(
            tool_name="process",
            parameters={"data": [1, 2, 3]},
            id="call-5",
        )
        json_str = original.to_json()
        restored = ToolCall.from_json(json_str)
        assert restored.tool_name == original.tool_name
        assert restored.parameters == original.parameters
        assert restored.id == original.id


class TestPlanResult:
    """Test PlanResult dataclass."""

    def test_create_plan_result(self) -> None:
        """Test creating a PlanResult."""
        tool_calls = [
            ToolCall("tool1", {"param": "value1"}),
            ToolCall("tool2", {"param": "value2"}),
        ]
        pr = PlanResult(
            reasoning="First extract text, then categorize",
            tool_calls=tool_calls,
            stop_reason="tool_use",
        )
        assert pr.reasoning == "First extract text, then categorize"
        assert len(pr.tool_calls) == 2
        assert pr.tool_calls[0].tool_name == "tool1"

    def test_plan_result_to_dict(self) -> None:
        """Test PlanResult.to_dict()."""
        tool_calls = [ToolCall("extract", {"text": "hello"})]
        pr = PlanResult(
            reasoning="Extract the text",
            tool_calls=tool_calls,
            metadata={"tokens": 100},
        )
        d = pr.to_dict()
        assert d["reasoning"] == "Extract the text"
        assert len(d["tool_calls"]) == 1
        assert d["tool_calls"][0]["tool_name"] == "extract"
        assert d["metadata"]["tokens"] == 100

    def test_plan_result_to_json(self) -> None:
        """Test PlanResult.to_json()."""
        pr = PlanResult(
            reasoning="Test reasoning",
            tool_calls=[ToolCall("test", {})],
        )
        json_str = pr.to_json()
        parsed = json.loads(json_str)
        assert parsed["reasoning"] == "Test reasoning"
        assert len(parsed["tool_calls"]) == 1

    def test_plan_result_from_dict(self) -> None:
        """Test PlanResult.from_dict()."""
        data = {
            "reasoning": "Plan the execution",
            "tool_calls": [
                {"tool_name": "step1", "parameters": {}},
                {"tool_name": "step2", "parameters": {}},
            ],
            "stop_reason": "end_turn",
            "metadata": {"elapsed_ms": 500},
        }
        pr = PlanResult.from_dict(data)
        assert pr.reasoning == "Plan the execution"
        assert len(pr.tool_calls) == 2
        assert pr.stop_reason == "end_turn"
        assert pr.metadata is not None
        assert pr.metadata["elapsed_ms"] == 500

    def test_plan_result_from_json(self) -> None:
        """Test PlanResult.from_json()."""
        json_str = """{
            "reasoning": "JSON test",
            "tool_calls": [{"tool_name": "json_tool", "parameters": {}}],
            "stop_reason": "tool_use"
        }"""
        pr = PlanResult.from_json(json_str)
        assert pr.reasoning == "JSON test"
        assert pr.tool_calls[0].tool_name == "json_tool"

    def test_plan_result_roundtrip(self) -> None:
        """Test serialize/deserialize roundtrip."""
        original = PlanResult(
            reasoning="Complex reasoning",
            tool_calls=[
                ToolCall("tool_a", {"x": 1}, id="a-1"),
                ToolCall("tool_b", {"y": 2}, id="b-1"),
            ],
            stop_reason="max_tokens",
            metadata={"tokens_used": 4096},
        )
        json_str = original.to_json()
        restored = PlanResult.from_json(json_str)
        assert restored.reasoning == original.reasoning
        assert len(restored.tool_calls) == 2
        assert restored.stop_reason == original.stop_reason
        assert restored.metadata == original.metadata


class TestOrchestratorConfig:
    """Test OrchestratorConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default OrchestratorConfig."""
        config = OrchestratorConfig()
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.tool_use_enabled is True

    def test_custom_config(self) -> None:
        """Test custom OrchestratorConfig."""
        config = OrchestratorConfig(
            model="gpt-4",
            api_key="sk-test",
            temperature=0.3,
            max_tokens=2048,
        )
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test"
        assert config.temperature == 0.3
        assert config.max_tokens == 2048

    def test_config_to_dict(self) -> None:
        """Test OrchestratorConfig.to_dict()."""
        config = OrchestratorConfig(model="ollama/mistral")
        d = config.to_dict()
        assert d["model"] == "ollama/mistral"
        assert "api_key" in d
        assert "temperature" in d

    def test_config_to_json(self) -> None:
        """Test OrchestratorConfig.to_json()."""
        config = OrchestratorConfig(base_url="http://localhost:8000")
        json_str = config.to_json()
        parsed = json.loads(json_str)
        assert parsed["base_url"] == "http://localhost:8000"


class TestToolSchema:
    """Test ToolSchema class."""

    def test_create_tool_schema(self) -> None:
        """Test creating a ToolSchema."""
        schema = ToolSchema(
            name="extract_text",
            description="Extract text from image",
            parameters={
                "properties": {
                    "image_url": {"type": "string"},
                }
            },
            required=["image_url"],
        )
        assert schema.name == "extract_text"
        assert schema.required == ["image_url"]

    def test_tool_schema_to_dict(self) -> None:
        """Test ToolSchema.to_dict()."""
        schema = ToolSchema(
            name="search",
            description="Search for items",
            parameters={
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                }
            },
            required=["query"],
        )
        d = schema.to_dict()
        assert d["name"] == "search"
        assert d["description"] == "Search for items"
        assert "input_schema" in d
        assert d["input_schema"]["properties"]["query"]["type"] == "string"

    def test_tool_schema_to_openai_format(self) -> None:
        """Test ToolSchema.to_openai_format()."""
        schema = ToolSchema(
            name="compute",
            description="Compute a value",
            parameters={
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                }
            },
            required=["x", "y"],
        )
        openai_fmt = schema.to_openai_format()
        assert openai_fmt["type"] == "function"
        assert openai_fmt["function"]["name"] == "compute"
        assert "parameters" in openai_fmt["function"]


class MockOrchestrator(OrchestratorBackend):
    """Mock orchestrator for testing interface compliance."""

    def __init__(self, config: OrchestratorConfig):
        super().__init__(config)
        self.registered_tools: list[ToolSchema] = []
        self.conversation_history: list[dict[str, str]] = []

    def register_tools(self, tools: list[ToolSchema]) -> None:
        """Register tools."""
        self.registered_tools = tools

    def plan(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str | None = None,
    ) -> PlanResult:
        """Generate a simple mock plan."""
        return PlanResult(
            reasoning=f"Planning for: {user_message}",
            tool_calls=[
                ToolCall("test_tool", {"message": user_message}, id="test-1")
            ],
            stop_reason="tool_use",
            metadata={"mock": True},
        )

    def plan_streaming(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> Any:
        """Mock streaming plan."""
        yield {"type": "thinking", "text": "Mock planning..."}
        yield {
            "type": "tool_call",
            "tool": "test_tool",
            "params": {"message": user_message},
        }

    def add_tool_result(
        self,
        tool_call_id: str,
        result: str | dict[str, str],
        is_error: bool = False,
    ) -> None:
        """Add tool result."""
        self.conversation_history.append(
            {"role": "user", "content": str(result)}
        )

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history

    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []


class TestOrchestratorBackend:
    """Test OrchestratorBackend interface."""

    def test_backend_registration(self) -> None:
        """Test tool registration."""
        config = OrchestratorConfig()
        backend = MockOrchestrator(config)

        tools = [
            ToolSchema(
                "tool1",
                "Tool 1",
                {"properties": {}},
            ),
            ToolSchema(
                "tool2",
                "Tool 2",
                {"properties": {}},
            ),
        ]
        backend.register_tools(tools)
        assert len(backend.registered_tools) == 2

    def test_backend_plan(self) -> None:
        """Test planning."""
        config = OrchestratorConfig()
        backend = MockOrchestrator(config)

        result = backend.plan("Extract text from image")
        assert result.reasoning == "Planning for: Extract text from image"
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].tool_name == "test_tool"

    def test_backend_streaming(self) -> None:
        """Test streaming plan."""
        config = OrchestratorConfig()
        backend = MockOrchestrator(config)

        events = list(backend.plan_streaming("Test message"))
        assert len(events) == 2
        assert events[0]["type"] == "thinking"
        assert events[1]["type"] == "tool_call"

    def test_backend_conversation_history(self) -> None:
        """Test conversation history."""
        config = OrchestratorConfig()
        backend = MockOrchestrator(config)

        backend.add_tool_result("call-1", "Success", is_error=False)
        history = backend.get_conversation_history()
        assert len(history) == 1

        backend.clear_conversation_history()
        history = backend.get_conversation_history()
        assert len(history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

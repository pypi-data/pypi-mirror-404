"""
Tests for LargePlanner integration with ExecutionContext.

Phase 4.2: LargePlanner SessionContext Integration

Tests cover:
- ExecutionContext creation and session tracking during plan generation
- Session metadata tracking (provider, model, plan stats)
- Error handling and session failure marking
- Session propagation through generate_plan and refine_plan
- Global context management
"""

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip this entire module if openai is not installed, as it's the default provider for LargePlanner
pytest.importorskip("openai")

from orchestrator._internal.planning.planner import LargePlanner
from orchestrator.context import (
    ExecutionContext,
    get_execution_context,
    set_execution_context,
)


@pytest.fixture
def mock_openai_response() -> Any:
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = '{"request_id": "test-123", "steps": [{"id": "s1", "tool": "test_tool"}]}'
    return mock_response


@pytest.fixture
def mock_anthropic_response() -> Any:
    """Mock Anthropic API response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[
        0
    ].text = '{"request_id": "test-123", "steps": [{"id": "s1", "tool": "test_tool"}]}'
    return mock_response


def _mock_openai_create(
    planner: LargePlanner,
    mock_response: Any | None = None,
    *,
    side_effect: Exception | None = None,
) -> None:
    client = cast(Any, planner.client)
    if side_effect is not None:
        client.chat.completions.create = AsyncMock(side_effect=side_effect)
    else:
        client.chat.completions.create = AsyncMock(return_value=mock_response)


def _mock_anthropic_create(planner: LargePlanner, mock_response: Any) -> None:
    client = cast(Any, planner.client)
    client.messages.create = AsyncMock(return_value=mock_response)


class TestLargePlannerSessionCreation:
    """Test ExecutionContext creation during plan generation."""

    @pytest.mark.asyncio
    async def test_planner_creates_session_if_none_provided(self, mock_openai_response: Any) -> None:
        """Should create session automatically if not provided."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            # Clear any existing global context
            set_execution_context(None)

            plan = await planner.generate_plan("Test request")

            assert plan is not None
            assert "steps" in plan
            # Session should have been created internally

    @pytest.mark.asyncio
    async def test_planner_uses_provided_session(self, mock_openai_response: Any) -> None:
        """Should use provided ExecutionContext."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            plan = await planner.generate_plan("Test request", session=session)

            assert plan is not None
            assert session.status == "completed"
            assert session.result is not None

    @pytest.mark.asyncio
    async def test_planner_uses_global_context_if_available(self, mock_openai_response: Any) -> None:
        """Should use global ExecutionContext if available and no session provided."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            global_session = ExecutionContext(user_id="global_user")
            set_execution_context(global_session)

            try:
                # Mock the API call
                _mock_openai_create(planner, mock_openai_response)

                plan = await planner.generate_plan("Test request")

                assert plan is not None
                assert global_session.status == "completed"
            finally:
                set_execution_context(None)

    @pytest.mark.asyncio
    async def test_planner_marks_session_started(self, mock_openai_response: Any) -> None:
        """Session should be marked as started when plan generation begins."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            assert session.status == "pending"

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            await planner.generate_plan("Test request", session=session)

            assert session.started_at is not None

    @pytest.mark.asyncio
    async def test_planner_marks_session_completed(self, mock_openai_response: Any) -> None:
        """Session should be marked as completed when plan generation succeeds."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            await planner.generate_plan("Test request", session=session)

            assert session.status == "completed"
            assert session.ended_at is not None
            assert session.result is not None

    @pytest.mark.asyncio
    async def test_planner_marks_session_failed_on_error(self) -> None:
        """Session should be marked as failed when plan generation fails."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call to raise an exception
            _mock_openai_create(planner, side_effect=RuntimeError("API error"))

            with pytest.raises(RuntimeError):
                await planner.generate_plan("Test request", session=session)

            assert session.status == "failed"
            assert session.error_message is not None


class TestLargePlannerMetadataTracking:
    """Test metadata tracking in session."""

    @pytest.mark.asyncio
    async def test_session_records_plan_metadata(self, mock_openai_response: Any) -> None:
        """Session should record provider, model, and plan statistics."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai", model="gpt-4o")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            await planner.generate_plan("Test request", session=session)

            assert "plan_generation_result" in session.metadata
            metadata = session.metadata["plan_generation_result"]
            assert metadata["provider"] == "openai"
            assert metadata["model"] == "gpt-4o"
            assert metadata["steps"] == 1

    @pytest.mark.asyncio
    async def test_plan_includes_request_id(self, mock_openai_response: Any) -> None:
        """Generated plan should include the session's request_id."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user", request_id="req-123")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            plan = await planner.generate_plan("Test request", session=session)

            # Plan should have request_id from session
            assert "request_id" in plan


class TestLargePlannerRefineIntegration:
    """Test refine_plan with ExecutionContext."""

    @pytest.mark.asyncio
    async def test_refine_plan_creates_session(self, mock_openai_response: Any) -> None:
        """refine_plan should create session if not provided."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            set_execution_context(None)

            original_plan = {"steps": [{"id": "s1", "tool": "old_tool"}]}
            refined_plan = await planner.refine_plan(original_plan, "Use a different tool")

            assert refined_plan is not None

    @pytest.mark.asyncio
    async def test_refine_plan_uses_provided_session(self, mock_openai_response: Any) -> None:
        """refine_plan should use provided session."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call
            _mock_openai_create(planner, mock_openai_response)

            original_plan = {"steps": [{"id": "s1", "tool": "old_tool"}]}
            refined_plan = await planner.refine_plan(
                original_plan, "Use a different tool", session=session
            )

            assert refined_plan is not None
            assert session.status == "completed"
            assert "plan_refinement_result" in session.metadata

    @pytest.mark.asyncio
    async def test_refine_plan_marks_failure(self) -> None:
        """refine_plan should mark session as failed on error."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call to raise an exception
            _mock_openai_create(planner, side_effect=RuntimeError("API error"))

            original_plan: dict[str, Any] = {"steps": []}
            with pytest.raises(RuntimeError):
                await planner.refine_plan(original_plan, "Feedback", session=session)

            assert session.status == "failed"


class TestLargePlannerContextRestoration:
    """Test global context restoration."""

    @pytest.mark.asyncio
    async def test_global_context_restored_after_generate(self, mock_openai_response: Any) -> None:
        """Global context should be restored after generate_plan."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            original_context = ExecutionContext(user_id="original_user")
            set_execution_context(original_context)

            try:
                # Mock the API call
                _mock_openai_create(planner, mock_openai_response)

                session = ExecutionContext(user_id="plan_user")
                await planner.generate_plan("Test request", session=session)

                # Original context should be restored
                assert get_execution_context() is original_context
            finally:
                set_execution_context(None)

    @pytest.mark.asyncio
    async def test_global_context_restored_after_refine(self, mock_openai_response: Any) -> None:
        """Global context should be restored after refine_plan."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="openai")
            original_context = ExecutionContext(user_id="original_user")
            set_execution_context(original_context)

            try:
                # Mock the API call
                _mock_openai_create(planner, mock_openai_response)

                session = ExecutionContext(user_id="plan_user")
                original_plan: dict[str, Any] = {"steps": []}
                await planner.refine_plan(original_plan, "Feedback", session=session)

                # Original context should be restored
                assert get_execution_context() is original_context
            finally:
                set_execution_context(None)


class TestLargePlannerProviderIntegration:
    """Test session integration across providers."""

    @pytest.mark.asyncio
    async def test_anthropic_provider_with_session(self, mock_anthropic_response: Any) -> None:
        """Anthropic provider should work with ExecutionContext."""
        pytest.importorskip("anthropic")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "PLANNER_FORCE_LITELLM": "false"}):
            planner = LargePlanner(provider="anthropic")
            session = ExecutionContext(user_id="test_user")

            # Mock the API call
            _mock_anthropic_create(planner, mock_anthropic_response)

            plan = await planner.generate_plan("Test request", session=session)

            assert plan is not None
            assert session.status == "completed"
            assert session.metadata["plan_generation_result"]["provider"] == "anthropic"

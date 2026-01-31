from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from orchestrator._internal.execution.small_model_worker import SmallModelWorker

# Ensure requests is available in sys.modules so imports in SmallModelWorker don't fail or warn
# (Though the code handles imports with try/except, patching is safer to avoid actual network calls)

@pytest.fixture
def mock_worker() -> Any:
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        # Mocking the generate method directly so we don't need real backend
        # We can construct it with backend='ollama' and it will try to connect
        # but our mock_get handles the connection check.

        # We need to ensure REQUESTS_AVAILABLE is True inside the module if we use backend='ollama'
        # But patching requests at module level is hard.
        # SmallModelWorker imports requests inside the try/except block at module level.
        # So we just instantiate it.

        with patch.object(SmallModelWorker, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "This is a summary."

            # Use 'transformers' to avoid requests call if possible?
            # transformers calls _init_transformers which demands transformers package
            # 'ollama' calls _init_ollama which calls requests.get

            # Let's mock _init_ollama validation
            with patch.object(SmallModelWorker, '_init_ollama'):
                worker = cast(Any, SmallModelWorker(backend="ollama", model_name="test-model"))
                worker.generate = mock_gen  # Ensure the method is the mock
                yield worker

def test_validate_regex(mock_worker: Any) -> None:
    """Test regex validation."""
    assert mock_worker.validate_regex("hello world", r"hello") is True
    assert mock_worker.validate_regex("hello world", r"^world") is False
    assert mock_worker.validate_regex("user@example.com", r"[\w\.-]+@[\w\.-]+") is True

    # Test invalid regex
    # It logs error but returns False
    assert mock_worker.validate_regex("test", r"[") is False

@pytest.mark.asyncio
async def test_summarize(mock_worker: Any) -> None:
    """Test summarize method delegates to generate."""
    text = "This is a long text " * 10
    summary = await mock_worker.summarize(text, max_words=20)

    assert summary == "This is a summary."

    # Verify generate called with correct prompt
    mock_worker.generate.assert_called_once()
    args, kwargs = mock_worker.generate.call_args
    prompt = args[0]
    system_prompt = args[1]

    assert "Text to summarize" in prompt
    assert text in prompt
    assert "under 20 words" in system_prompt

@pytest.mark.asyncio
async def test_summarize_with_focus(mock_worker: Any) -> None:
    """Test summarize method with focus parameter."""
    text = "Content about specific topic."
    await mock_worker.summarize(text, focus="Topic X")

    args, kwargs = mock_worker.generate.call_args
    system_prompt = args[1]
    assert "Focus on: Topic X" in system_prompt

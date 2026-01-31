"""
Tests for Context Analyzer (RLM Mode Selection).

Tests token estimation, complexity assessment, RLM mode selection,
strategy selection, and recursion depth estimation.
"""

from typing import Any

import pytest

from orchestrator.skills.task_planning.context_analyzer import (
    ContextAnalysis,
    ContextAnalyzer,
    RLMStrategy,
    analyze_context,
)


@pytest.fixture
def analyzer() -> Any:
    """Create analyzer with test configuration."""
    return ContextAnalyzer(
        context_threshold_tokens=128000,
        tokens_per_char=0.25,
        debug=True,
    )


@pytest.fixture
def small_context() -> Any:
    """Small context (< threshold)."""
    # ~10k chars = ~2.5k tokens
    return "x" * 10_000


@pytest.fixture
def large_context() -> Any:
    """Large context (> threshold)."""
    # ~600k chars = ~150k tokens (exceeds 128k threshold)
    return "x" * 600_000


@pytest.fixture
def structured_json_context() -> Any:
    """Structured JSON-like context."""
    return (
        """
    [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie", "age": 35}
    ]
    """
        * 1000
    )  # Repeat to make it substantial


class TestTokenEstimation:
    """Test token estimation logic."""

    def test_estimate_tokens_simple(self) -> None:
        """Test basic token estimation."""
        text = "x" * 1000  # 1000 chars
        tokens = ContextAnalyzer.estimate_tokens(text, tokens_per_char=0.25)
        assert tokens == 250  # 1000 * 0.25 = 250

    def test_estimate_tokens_custom_ratio(self) -> None:
        """Test token estimation with custom ratio."""
        text = "x" * 1000
        tokens = ContextAnalyzer.estimate_tokens(text, tokens_per_char=0.5)
        assert tokens == 500  # 1000 * 0.5 = 500

    def test_estimate_tokens_empty(self) -> None:
        """Test token estimation with empty text."""
        tokens = ContextAnalyzer.estimate_tokens("", tokens_per_char=0.25)
        assert tokens == 0

    def test_estimate_tokens_unicode(self) -> None:
        """Test token estimation with unicode."""
        text = "你好世界" * 100  # Chinese characters
        tokens = ContextAnalyzer.estimate_tokens(text, tokens_per_char=0.25)
        assert tokens > 0  # Should estimate something


class TestComplexityAssessment:
    """Test task complexity assessment."""

    def test_assess_complexity_simple(self, analyzer: Any) -> None:
        """Test simple task classification."""
        task = "Tell me a joke"
        complexity = analyzer._assess_complexity(task)
        assert complexity == "simple"

    def test_assess_complexity_moderate(self, analyzer: Any) -> None:
        """Test moderate task classification."""
        task = "Locate all email addresses and retrieve them from the log file"
        complexity = analyzer._assess_complexity(task)
        assert complexity == "moderate"

    def test_assess_complexity_complex(self, analyzer: Any) -> None:
        """Test complex task classification."""
        task = "Find all users who made purchases between 2020 and 2025 and aggregate their total spend"
        complexity = analyzer._assess_complexity(task)
        assert complexity == "complex"

    def test_assess_complexity_multi_hop(self, analyzer: Any) -> None:
        """Test multi-hop task classification."""
        task = "Count how many times each author appears across all documents"
        complexity = analyzer._assess_complexity(task)
        assert complexity == "complex"


class TestRLMModeSelection:
    """Test RLM mode selection logic (adaptive, always, off)."""

    def test_mode_always_forces_rlm(self, analyzer: Any, small_context: Any) -> None:
        """Test RLM_MODE=always forces RLM even for small contexts."""
        task = "Simple task"
        analysis = analyzer.analyze(task, small_context, rlm_mode="always")

        assert analysis.use_rlm is True
        assert "always" in analysis.reason
        assert analysis.estimated_tokens < analyzer.context_threshold_tokens

    def test_mode_off_disables_rlm(self, analyzer: Any, large_context: Any) -> None:
        """Test RLM_MODE=off disables RLM even for large contexts."""
        task = "Complex multi-hop task"
        analysis = analyzer.analyze(task, large_context, rlm_mode="off")

        assert analysis.use_rlm is False
        assert "off" in analysis.reason
        assert analysis.estimated_tokens > analyzer.context_threshold_tokens

    def test_mode_adaptive_small_context(self, analyzer: Any, small_context: Any) -> None:
        """Test adaptive mode with small context (below threshold)."""
        task = "Simple task"
        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        assert analysis.use_rlm is False
        assert "adaptive" in analysis.reason
        assert analysis.estimated_tokens < analyzer.context_threshold_tokens

    def test_mode_adaptive_large_context(self, analyzer: Any, large_context: Any) -> None:
        """Test adaptive mode with large context (above threshold)."""
        task = "Simple task"
        analysis = analyzer.analyze(task, large_context, rlm_mode="adaptive")

        assert analysis.use_rlm is True
        assert "adaptive" in analysis.reason
        assert analysis.estimated_tokens > analyzer.context_threshold_tokens

    def test_mode_adaptive_complex_task_small_context(self, analyzer: Any, small_context: Any) -> None:
        """Test adaptive mode with complex task on small context."""
        task = "Find all users who made purchases between dates and aggregate their spend"
        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        # Complex task may trigger RLM even with smaller context
        # Depends on strategy selection
        assert isinstance(analysis.use_rlm, bool)
        assert "adaptive" in analysis.reason


class TestStrategySelection:
    """Test RLM strategy selection (peek, grep, partition, programmatic)."""

    def test_strategy_programmatic_git_diff(self, analyzer: Any) -> None:
        """Test programmatic strategy for git diff tasks."""
        task = "Show me the git diff between commit A and commit B"
        context = "git repository data here"

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")
        assert analysis.suggested_strategy == RLMStrategy.PROGRAMMATIC

    def test_strategy_programmatic_multiplication(self, analyzer: Any) -> None:
        """Test programmatic strategy for multiplication tasks."""
        task = "Multiply 12345 * 67890"
        context = "numbers"

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")
        assert analysis.suggested_strategy == RLMStrategy.PROGRAMMATIC

    def test_strategy_grep_search(self, analyzer: Any) -> None:
        """Test grep strategy for search tasks."""
        task = "Find all entries matching the pattern ERROR"
        context = "log file content"

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")
        assert analysis.suggested_strategy == RLMStrategy.GREP

    def test_strategy_grep_structured_data(self, analyzer: Any, structured_json_context: Any) -> None:
        """Test grep strategy for structured data."""
        task = "Extract user names"
        analysis = analyzer.analyze(task, structured_json_context, rlm_mode="adaptive")

        assert analysis.suggested_strategy == RLMStrategy.GREP

    def test_strategy_partition_large_context(self, analyzer: Any, large_context: Any) -> None:
        """Test partition strategy for large contexts."""
        task = "Analyze and explain this content"
        analysis = analyzer.analyze(task, large_context, rlm_mode="adaptive")

        # Large context (if not structured-looking) should suggest partition
        # Note: repeated 'x' chars may not look structured, should get PARTITION
        assert analysis.suggested_strategy in [RLMStrategy.PARTITION, RLMStrategy.GREP]
        if analysis.suggested_strategy == RLMStrategy.PARTITION:
            assert analysis.suggested_chunk_size is not None
            assert analysis.suggested_chunk_size > 0

    def test_strategy_traditional_small_context(self, analyzer: Any, small_context: Any) -> None:
        """Test traditional strategy for small simple tasks."""
        task = "Tell me about this"
        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        assert analysis.suggested_strategy == RLMStrategy.TRADITIONAL


class TestRecursionDepthEstimation:
    """Test recursion depth estimation."""

    def test_depth_normal_context(self, analyzer: Any) -> None:
        """Test depth=1 for normal sized contexts."""
        context = "x" * 500_000  # ~125k tokens (near threshold)
        task = "Analyze this"

        analysis = analyzer.analyze(task, context, rlm_mode="always")
        assert analysis.estimated_recursion_depth == 1

    def test_depth_1m_token_context(self, analyzer: Any) -> None:
        """Test depth=1 for 1M token contexts."""
        context = "x" * 4_000_000  # ~1M tokens
        task = "Analyze this"

        analysis = analyzer.analyze(task, context, rlm_mode="always")
        assert analysis.estimated_recursion_depth == 1

    def test_depth_10m_token_context(self, analyzer: Any) -> None:
        """Test depth=2 for contexts above 10M tokens."""
        context = "x" * 50_000_000  # ~12.5M tokens (above 10M threshold)
        task = "Analyze this"

        analysis = analyzer.analyze(task, context, rlm_mode="always")
        assert analysis.estimated_recursion_depth == 2


class TestChunkSizeRecommendation:
    """Test chunk size recommendations for partition strategy."""

    def test_chunk_size_calculated(self, analyzer: Any) -> None:
        """Test chunk size is calculated for partition strategy."""
        chunk_size = analyzer._suggest_chunk_size(estimated_tokens=1_000_000)

        # Should be ~320k chars (80k tokens * 4 chars/token)
        assert chunk_size > 0
        assert 300_000 < chunk_size < 400_000

    def test_partition_includes_chunk_size(self, analyzer: Any, large_context: Any) -> None:
        """Test partition strategy includes chunk size in analysis."""
        task = "Summarize everything"
        analysis = analyzer.analyze(task, large_context, rlm_mode="always")

        if analysis.suggested_strategy == RLMStrategy.PARTITION:
            assert analysis.suggested_chunk_size is not None
            assert analysis.suggested_chunk_size > 0


class TestContextAnalysisDataclass:
    """Test ContextAnalysis dataclass structure."""

    def test_analysis_has_all_fields(self, analyzer: Any, small_context: Any) -> None:
        """Test analysis returns all expected fields."""
        task = "Test task"
        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        assert hasattr(analysis, "estimated_tokens")
        assert hasattr(analysis, "context_size_bytes")
        assert hasattr(analysis, "task_complexity")
        assert hasattr(analysis, "suggested_strategy")
        assert hasattr(analysis, "use_rlm")
        assert hasattr(analysis, "reason")
        assert hasattr(analysis, "estimated_recursion_depth")
        assert hasattr(analysis, "suggested_chunk_size")

    def test_analysis_types(self, analyzer: Any, small_context: Any) -> None:
        """Test analysis field types are correct."""
        task = "Test task"
        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        assert isinstance(analysis.estimated_tokens, int)
        assert isinstance(analysis.context_size_bytes, int)
        assert isinstance(analysis.task_complexity, str)
        assert isinstance(analysis.suggested_strategy, RLMStrategy)
        assert isinstance(analysis.use_rlm, bool)
        assert isinstance(analysis.reason, str)
        assert isinstance(analysis.estimated_recursion_depth, int)


class TestConvenienceFunction:
    """Test analyze_context convenience function."""

    def test_analyze_context_uses_env_mode(self, monkeypatch: Any, small_context: Any) -> None:
        """Test convenience function respects RLM_MODE env var."""
        monkeypatch.setenv("RLM_MODE", "always")

        task = "Test task"
        analysis = analyze_context(task, small_context)

        assert analysis.use_rlm is True
        assert "always" in analysis.reason

    def test_analyze_context_explicit_mode(self, small_context: Any) -> None:
        """Test convenience function with explicit mode."""
        task = "Test task"
        analysis = analyze_context(task, small_context, rlm_mode="off")

        assert analysis.use_rlm is False
        assert "off" in analysis.reason

    def test_analyze_context_dict_context(self) -> None:
        """Test convenience function with dict context."""
        task = "Analyze this data"
        context = {"key": "value", "numbers": [1, 2, 3]}

        analysis = analyze_context(task, context, rlm_mode="adaptive")

        assert isinstance(analysis, ContextAnalysis)
        assert analysis.context_size_bytes > 0


class TestStructuredDataDetection:
    """Test detection of structured data."""

    def test_looks_structured_json(self, analyzer: Any) -> None:
        """Test structured detection for JSON."""
        context = '{"key": "value"}\n' * 200
        assert analyzer._looks_structured(context) is True

    def test_looks_structured_csv(self, analyzer: Any) -> None:
        """Test structured detection for CSV."""
        context = "a,b,c,d,e,f\n1,2,3,4,5,6\n" * 500  # More commas per line, more lines
        assert analyzer._looks_structured(context) is True

    def test_looks_unstructured_prose(self, analyzer: Any) -> None:
        """Test unstructured detection for prose."""
        context = "This is a paragraph of text. " * 200
        assert analyzer._looks_structured(context) is False

    def test_looks_unstructured_short(self, analyzer: Any) -> None:
        """Test short text is not considered structured."""
        context = '{"key": "value"}\n' * 10  # Only 10 lines
        assert analyzer._looks_structured(context) is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_context(self, analyzer: Any) -> None:
        """Test analysis with empty context."""
        task = "Do something"
        context = ""

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")

        assert analysis.estimated_tokens == 0
        assert analysis.context_size_bytes == 0
        assert analysis.use_rlm is False  # Empty context should not trigger RLM

    def test_empty_task(self, analyzer: Any, small_context: Any) -> None:
        """Test analysis with empty task."""
        task = ""

        analysis = analyzer.analyze(task, small_context, rlm_mode="adaptive")

        assert isinstance(analysis, ContextAnalysis)
        assert analysis.task_complexity == "simple"

    def test_exact_threshold_boundary(self, analyzer: Any) -> None:
        """Test behavior at exact threshold boundary."""
        # Create context exactly at threshold: 128000 tokens = 512000 chars
        context = "x" * 512_000
        task = "Test"

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")

        # At or above threshold should trigger RLM
        assert analysis.estimated_tokens >= analyzer.context_threshold_tokens
        assert analysis.use_rlm is True

    def test_dict_context_conversion(self, analyzer: Any) -> None:
        """Test dict context is converted to string."""
        task = "Analyze this"
        context = {"nested": {"key": "value"}, "list": [1, 2, 3]}

        analysis = analyzer.analyze(task, context, rlm_mode="adaptive")

        assert analysis.estimated_tokens > 0
        assert analysis.context_size_bytes > 0

"""
Context Analyzer for RLM Mode Selection.

Analyzes task and context to determine:
1. Whether RLM mode should be used
2. Estimated token count
3. Estimated recursion depth needed
4. Fallback strategy (peek, grep, partition)

Based on: Recursive Language Models (Zhang et al., Dec 2025)
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RLMStrategy(str, Enum):
    """Strategies that emerge in RLM execution."""

    PEEK = "peek"  # Examine first N chars to understand structure
    GREP = "grep"  # Use regex to narrow search space
    PARTITION = "partition"  # Split context, recurse on chunks
    SUMMARIZE = "summarize"  # Summarize portions for outer LM
    PROGRAMMATIC = "programmatic"  # Execute code directly (git diff, multiplication)
    TRADITIONAL = "traditional"  # Skip RLM, use traditional planning


@dataclass
class ContextAnalysis:
    """Analysis of task context to guide RLM decisions."""

    estimated_tokens: int
    context_size_bytes: int
    task_complexity: str  # simple, moderate, complex
    suggested_strategy: RLMStrategy
    use_rlm: bool  # Whether RLM is recommended
    reason: str  # Why this decision was made
    estimated_recursion_depth: int = 1
    suggested_chunk_size: int | None = None


class ContextAnalyzer:
    """Analyzes task context to determine RLM eligibility and strategy."""

    # Patterns that suggest different strategies
    GREP_PATTERNS = {
        "structured_search": r"(find|search|locate|look for|match|filter)",
        "multi_hop": r"(how many|count|aggregate|sum|group|between)",
        "semantic": r"(meaning|implies|related|similar|difference)",
    }

    PROGRAMMATIC_PATTERNS = {
        "git_diff": r"(git|diff|patch|version control|commit)",
        "multiplication": r"(multiply|product|\d+\s*×\s*\d+)",
        "sequence": r"(sequence|order|sort|reverse|transpose)",
    }

    def __init__(
        self,
        context_threshold_tokens: int = 128000,
        tokens_per_char: float = 0.25,
        debug: bool = False,
    ):
        """
        Initialize analyzer.

        Args:
            context_threshold_tokens: Minimum tokens to trigger RLM
            tokens_per_char: Conversion factor for estimation
            debug: Enable debug logging
        """
        self.context_threshold_tokens = context_threshold_tokens
        self.tokens_per_char = tokens_per_char
        self.debug = debug

    @staticmethod
    def estimate_tokens(text: str, tokens_per_char: float = 0.25) -> int:
        """Estimate token count from character count."""
        return int(len(text) * tokens_per_char)

    def analyze(
        self,
        task: str,
        context: str | dict[str, Any],
        rlm_mode: str = "adaptive",
    ) -> ContextAnalysis:
        """
        Analyze task and context to determine RLM suitability.

        Args:
            task: Task description (natural language)
            context: The context (string or dict)
            rlm_mode: "adaptive", "always", "off"

        Returns:
            ContextAnalysis with recommendations
        """
        # Convert context to string if needed
        context_str = context if isinstance(context, str) else str(context)
        context_bytes = len(context_str.encode("utf-8"))
        estimated_tokens = self.estimate_tokens(context_str, self.tokens_per_char)

        if self.debug:
            logger.debug(
                f"Context analysis: {context_bytes} bytes, ~{estimated_tokens} tokens estimated"
            )

        # Determine task complexity from patterns
        task_lower = task.lower()
        complexity = self._assess_complexity(task_lower)

        # Suggest strategy based on task/context
        strategy = self._suggest_strategy(task_lower, context_str)

        # Apply RLM mode logic
        if rlm_mode == "always":
            use_rlm = True
            reason = "RLM_MODE=always (forced)"
        elif rlm_mode == "off":
            use_rlm = False
            reason = "RLM_MODE=off (disabled)"
        else:  # adaptive
            # Use RLM if context exceeds threshold OR task is complex multi-hop
            use_rlm = estimated_tokens >= self.context_threshold_tokens or (
                complexity == "complex" and strategy != RLMStrategy.TRADITIONAL
            )
            reason = (
                f"adaptive mode: {estimated_tokens} tokens "
                f"(threshold: {self.context_threshold_tokens}), "
                f"complexity: {complexity}"
            )

        # Estimate recursion depth
        recursion_depth = self._estimate_recursion_depth(
            estimated_tokens,
            strategy,
        )

        # Suggest chunk size if partitioning
        chunk_size = None
        if strategy == RLMStrategy.PARTITION:
            chunk_size = self._suggest_chunk_size(estimated_tokens)

        if self.debug:
            logger.debug(
                f"Analysis: complexity={complexity}, strategy={strategy.value}, "
                f"use_rlm={use_rlm}, depth={recursion_depth}"
            )

        return ContextAnalysis(
            estimated_tokens=estimated_tokens,
            context_size_bytes=context_bytes,
            task_complexity=complexity,
            suggested_strategy=strategy,
            use_rlm=use_rlm,
            reason=reason,
            estimated_recursion_depth=recursion_depth,
            suggested_chunk_size=chunk_size,
        )

    @staticmethod
    def _assess_complexity(task: str) -> str:
        """Assess task complexity from text patterns."""
        if any(
            word in task
            for word in [
                "aggregate",
                "multi-hop",
                "across",
                "relate",
                "between",
                "find",
                "count",
            ]
        ):
            return "complex"
        elif any(word in task for word in ["extract", "locate", "retrieve", "search"]):
            return "moderate"
        else:
            return "simple"

    def _suggest_strategy(self, task: str, context: str) -> RLMStrategy:
        """Suggest best strategy for this task/context combination."""
        # Check for programmatic tasks (likely one-shot)
        for pattern in self.PROGRAMMATIC_PATTERNS.values():
            if re.search(pattern, task, re.IGNORECASE):
                return RLMStrategy.PROGRAMMATIC

        # Check for grep-style searches
        for pattern in self.GREP_PATTERNS.values():
            if re.search(pattern, task, re.IGNORECASE):
                return RLMStrategy.GREP

        # Check if context appears structured
        if self._looks_structured(context):
            return RLMStrategy.GREP

        # Default to partition for large contexts
        context_tokens = self.estimate_tokens(context, self.tokens_per_char)
        if context_tokens > self.context_threshold_tokens:
            return RLMStrategy.PARTITION

        return RLMStrategy.TRADITIONAL

    @staticmethod
    def _looks_structured(context: str) -> bool:
        """Check if context appears to be structured data (JSON, CSV, etc)."""
        # Look for common delimiters
        json_chars = context.count("{") + context.count("}")
        csv_chars = context.count(",")
        yaml_chars = context.count(":")

        total_lines = len(context.split("\n"))

        # If significant structure, likely data
        if total_lines > 100 and (json_chars + csv_chars + yaml_chars) > total_lines * 2:
            return True

        return False

    @staticmethod
    def _estimate_recursion_depth(
        estimated_tokens: int,
        strategy: RLMStrategy,
    ) -> int:
        """Estimate recursion depth needed."""
        # RLM paper shows depth=1 sufficient for most cases
        # Only increase for extremely large contexts
        if estimated_tokens > 10_000_000:  # 10M tokens
            return 2
        if estimated_tokens > 1_000_000:  # 1M tokens
            return 1
        return 1

    @staticmethod
    def _suggest_chunk_size(estimated_tokens: int) -> int:
        """Suggest chunk size for partition strategy."""
        # Each recursive call can handle ~100k tokens comfortably
        # Chunk to 80k tokens to leave safety margin
        tokens_per_chunk = 80_000
        chars_per_token = 1 / 0.25  # ~4 chars per token
        chunk_size_chars = int(tokens_per_chunk * chars_per_token)
        return chunk_size_chars


# Global instance (for config-driven mode selection)
_analyzer_instance: ContextAnalyzer | None = None


def get_analyzer() -> ContextAnalyzer:
    """Get or create global analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        threshold = int(os.getenv("RLM_CONTEXT_THRESHOLD_TOKENS", "128000"))
        debug = os.getenv("RLM_DEBUG", "false").lower() == "true"
        _analyzer_instance = ContextAnalyzer(
            context_threshold_tokens=threshold,
            debug=debug,
        )
    return _analyzer_instance


def analyze_context(
    task: str,
    context: str | dict[str, Any],
    rlm_mode: str | None = None,
) -> ContextAnalysis:
    """Convenience function to analyze context with current config."""
    if rlm_mode is None:
        rlm_mode = os.getenv("RLM_MODE", "adaptive")

    analyzer = get_analyzer()
    return analyzer.analyze(task, context, rlm_mode)

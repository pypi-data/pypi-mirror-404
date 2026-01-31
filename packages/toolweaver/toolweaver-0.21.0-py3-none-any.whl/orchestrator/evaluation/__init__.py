"""
Evaluation Framework for ToolWeaver

Provides suite-based evaluation of API endpoints and skill execution
with configurable tolerance, regex matching, and artifact generation.
"""

from .runner import EvaluationResult, EvaluationRunner

__all__ = ["EvaluationRunner", "EvaluationResult"]

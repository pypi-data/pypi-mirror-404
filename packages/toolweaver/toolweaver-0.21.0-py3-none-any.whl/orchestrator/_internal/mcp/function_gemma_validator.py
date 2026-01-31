"""
Function Gemma Validator (Phase 7.2)

Uses a small, specialized model (Function Gemma via Ollama) to validate
tool calls before execution. This acts as a "sanity check" layer, protecting
against hallucinations or malformed parameters from larger but less strict models.

Features:
- Validates tool call parameters against schema descriptions
- "Corrects" minor errors (e.g. string vs int, missing optional fields)
- Modes:
    - ADVISORY: Log warnings but allow execution
    - STRICT: Block execution if validation fails
    - DISABLED: Passthrough

Model: google/gemma-2-9b-it (or similar function-calling optimized variants)
Interface: Uses Ollama API (via requests or library)
"""

import json
import logging
import os
from enum import Enum
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ValidationMode(Enum):
    DISABLED = "disabled"
    ADVISORY = "advisory"
    STRICT = "strict"


class ToolValidator:
    """Validates tool calls using a local LLM."""

    def __init__(
        self,
        mode: ValidationMode = ValidationMode.ADVISORY,
        model_name: str = "gemma:2b", # Small, fast default
        base_url: str | None = None,
    ):
        self.mode = mode
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.enabled = mode != ValidationMode.DISABLED

    def validate(
        self,
        tool_name: str,
        params: dict[str, Any],
        schema: dict[str, Any]
    ) -> tuple[bool, dict[str, Any], str | None]:
        """
        Validate tool parameters against schema.

        Args:
            tool_name: Name of tool
            params: Parameters to validate
            schema: Tool's JSON schema

        Returns:
            Tuple of (is_valid, corrected_params, error_reason)
        """
        if not self.enabled:
            return True, params, None

        prompt = self._build_validation_prompt(tool_name, params, schema)

        try:
            response = self._query_ollama(prompt)
            return self._parse_validation_response(response, params)
        except Exception as e:
            logger.warning(f"Validation failed (system error): {e}")
            # Fail open in advisory, fail closed in strict?
            # Usually fail open for resilience unless strict security required.
            if self.mode == ValidationMode.STRICT:
                return False, params, f"Validator error: {e}"
            return True, params, None

    def _build_validation_prompt(
        self,
        tool_name: str,
        params: dict[str, Any],
        schema: dict[str, Any]
    ) -> str:
        """Construct prompt for the validator model."""
        return f"""
You are a strict API validator. Check if the parameters match the schema.
Tool: {tool_name}
Schema: {json.dumps(schema, indent=2)}
Parameters: {json.dumps(params, indent=2)}

Task:
1. Check types (string, int, boolean)
2. Check required fields
3. Check constraints (enums, ranges)

Return ONLY a JSON object with this format:
{{
  "valid": boolean,
  "reason": "explanation of error or null",
  "corrected": {{ ...corrected parameters... }}
}}
"""

    def _query_ollama(self, prompt: str) -> str:
        """Send query to Ollama."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json" # Force JSON output
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return str(response.json()["response"])

    def _parse_validation_response(
        self,
        llm_output: str,
        original_params: dict[str, Any]
    ) -> tuple[bool, dict[str, Any], str | None]:
        """Parse LLM JSON output."""
        try:
            result = json.loads(llm_output)
            is_valid = result.get("valid", False)
            reason = result.get("reason")
            corrected = result.get("corrected", original_params)

            if is_valid:
                return True, corrected, None

            # Validation failed
            if self.mode == ValidationMode.STRICT:
                logger.error(f"Validation blocked tool call: {reason}")
                return False, original_params, reason
            else:
                logger.warning(f"Validation warning: {reason}")
                # In advisory, we might still use corrected params if they look safe?
                # Or adhere to original? Let's use corrected as "best effort fix"
                return True, corrected, reason

        except json.JSONDecodeError:
            logger.warning("Validator returned invalid JSON")
            return True, original_params, None


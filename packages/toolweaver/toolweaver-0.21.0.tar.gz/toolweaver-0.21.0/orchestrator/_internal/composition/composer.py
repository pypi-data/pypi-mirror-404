"""
LLM Composer for Programmatic Tool Calling.

Generates Python orchestration code from natural language goals.
"""

import logging
import re

from orchestrator._internal.workflows.control_flow_patterns import ControlFlowPatterns
from orchestrator.adapters.orchestrator_interface import OrchestratorBackend
from orchestrator.shared.models import ToolCatalog

from .prompts import COMPOSITION_SYSTEM_PROMPT, COMPOSITION_USER_PROMPT

logger = logging.getLogger(__name__)


class TaskComposer:
    """
    Composes executable plans (Python code) from natural language goals.
    """

    def __init__(
        self,
        backend: OrchestratorBackend,
        tool_catalog: ToolCatalog,
    ):
        """
        Initialize the composer.

        Args:
            backend: LLM backend for generation (Claude, OpenAI, etc.)
            tool_catalog: Catalog of available tools
        """
        self.backend = backend
        self.tool_catalog = tool_catalog
        # We assume stubs are transient or allow generator to work in memory
        # CodeGenerator actually writes to disk, but we might want to just get the format
        # For now, let's just generate a text summary of tools manually or use a helper
        # from CodeGenerator if available.

        # CodeGenerator requires an output dir, but we might not want to write files just to get definitions.
        # Let's inspect CodeGenerator again or implement a lightweight definition generator here.

    def generate_plan(self, goal: str) -> str:
        """
        Generate Python code to achieve the goal.

        Args:
            goal: User's task description

        Returns:
            Executable Python code string
        """
        logger.info(f"Composing plan for goal: {goal}")

        # 1. Prepare Context
        tool_defs = self._format_tool_definitions()
        patterns = self._format_control_flow()

        # 2. Build Prompt
        system_prompt = COMPOSITION_SYSTEM_PROMPT.format(
            tool_definitions=tool_defs,
            control_flow_patterns=patterns
        )
        user_prompt = COMPOSITION_USER_PROMPT.format(goal=goal)

        # 3. Call LLM
        # We use plan() but ignore tool_calls since we want the text (code) in reasoning
        # Ideally, we should disable tool usage for this call if the backend supports it,
        # but pure text response is also fine.
        result = self.backend.plan(
            user_message=user_prompt,
            system_prompt=system_prompt
        )

        # 4. Extract Code
        code = self._extract_code(result.reasoning)

        if not code:
            # Fallback: sometimes code might be in result.metadata or elsewhere if reasoning is empty?
            # Or if the model returned tools despite instructions.
            logger.warning("No code found in reasoning. Model response might be malformed.")
            if result.reasoning:
                logger.debug(f"Reasoning content: {result.reasoning}")

            # Simple fallback check if reasoning IS the code
            if "def " in result.reasoning or "async " in result.reasoning:
                 return result.reasoning

            raise ValueError("Failed to generate code plan from LLM response")

        return code

    def _format_tool_definitions(self) -> str:
        """Format tools for the system prompt."""
        # Simple Python-like signature generation
        lines = []
        for name, tool in self.tool_catalog.tools.items():
            params = []
            # Handle list of ToolParameter objects
            if hasattr(tool, "parameters") and isinstance(tool.parameters, list):
                for param in tool.parameters:
                    # ToolParameter has name, type, description, required
                    ptype = param.type  # e.g. "string"
                    # Map JSON types to python types vaguely
                    type_map = {
                        "string": "str",
                        "integer": "int",
                        "number": "float",
                        "boolean": "bool",
                        "array": "list",
                        "object": "dict"
                    }
                    py_type = type_map.get(ptype, ptype)
                    if not param.required:
                        py_type = f"Optional[{py_type}]"

                    params.append(f"{param.name}: {py_type}")

            # Fallback to input_schema if parameters list is empty (legacy/dynamic)
            elif tool.input_schema and "properties" in tool.input_schema:
                 props = tool.input_schema.get("properties", {})
                 for pname, pdef in props.items():
                     ptype = pdef.get("type", "Any")
                     params.append(f"{pname}: {ptype}")

            sig = f"async def {name}({', '.join(params)}) -> Any:"
            lines.append(sig)
            if tool.description:
                lines.append(f'    """{tool.description}"""')
            lines.append("    ...")
            lines.append("")

        return "\n".join(lines)

    def _format_control_flow(self) -> str:
        """Format control flow patterns."""
        patterns = ControlFlowPatterns.list_patterns()
        lines = []
        for p in patterns:
            lines.append(f"Pattern: {p.type.name} ({p.description})")
            lines.append(f"Template:\n{p.code_template}")
            lines.append("---")
        return "\n".join(lines)

    def _extract_code(self, text: str) -> str:
        """Extract code from markdown block."""
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try generic block
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return ""

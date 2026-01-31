"""
Large Model Planner - Uses GPT-4o or Claude to generate execution plans.

This module provides a high-level planner that uses large language models
to convert natural language requests into structured execution plans.
"""

import asyncio
import json
import logging
import os
import warnings
from types import TracebackType
from typing import Any, cast

from dotenv import load_dotenv

from orchestrator.context import ExecutionContext, get_execution_context, set_execution_context
from orchestrator.shared.models import ToolCatalog, ToolDefinition, ToolParameter
from orchestrator.tools.discovery_api import get_registry_tool_catalog

logger = logging.getLogger(__name__)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    load_dotenv(override=False)

# Configure LiteLLM logging properly
litellm_log_level = os.getenv("LITELLM_LOG", os.getenv("LITELLM_LOG_LEVEL", "WARNING")).upper()
litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(getattr(logging, litellm_log_level, logging.WARNING))
litellm_logger.propagate = True

# Optional imports - only loaded if needed (warnings shown when actually used)
try:
    from openai import AsyncAzureOpenAI, AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

genai: Any | None = None
try:
    # Use new google.genai SDK
    import google.genai as _genai

    genai = _genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def _normalize_gemini_model_name(name: str) -> str:
    """Ensure google.genai models use the required 'models/' prefix."""
    if not name:
        return name

    return name if name.startswith("models/") else f"models/{name}"


def _gemini_model_candidates(raw_name: str) -> list[str]:
    base = raw_name[len("models/") :] if raw_name.startswith("models/") else raw_name
    seen: set[str] = set()
    candidates: list[str] = []
    for suffix in ("", "-latest"):
        for prefix in ("models/", ""):
            candidate = f"{prefix}{base}{suffix}" if prefix else f"{base}{suffix}"
            if candidate and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)
    return candidates

try:
    import litellm

    # Disable LiteLLM's verbose logging by setting the environment variable
    # (litellm doesn't explicitly export set_verbose attribute)
    os.environ["LITELLM_LOG"] = "none"

    # Suppress LiteLLM's logger (uses "LiteLLM" as logger name)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class LargePlanner:
    """
    Uses a large language model (GPT-4o, Claude 3.5) to generate execution plans
    from natural language user requests.

    The planner understands available tools and generates JSON plans with:
    - Step definitions (tool type, inputs, dependencies)
    - Dependency resolution (DAG structure)
    - Parallel vs sequential execution modes
    """

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        tool_catalog: ToolCatalog | None = None,
        use_registry_catalog: bool = False,
        registry_catalog_use_cache: bool = True,
        use_tool_search: bool = True,
        search_threshold: int = 20,
        use_programmatic_calling: bool = True,
        session: ExecutionContext | None = None,
    ):
        """
        Initialize the planner with specified LLM provider.

        Args:
            provider: "openai", "azure-openai", "anthropic", or "gemini" (defaults to PLANNER_PROVIDER env var)
            model: Specific model name (defaults to PLANNER_MODEL env var)
            tool_catalog: Optional ToolCatalog with tool definitions (defaults to legacy hardcoded tools)
            use_registry_catalog: If True, build catalog from the configured tool registry (local/sqlite/redis)
            registry_catalog_use_cache: If True, reuse cached registry catalog per backend
            use_tool_search: Enable semantic search for tool selection (Phase 3, default: True)
            search_threshold: Only use search if tool count exceeds this (default: 20)
            use_programmatic_calling: Enable programmatic tool calling (Phase 4, default: True)

        Phase 2 Usage - Tool Discovery:
            To use auto-discovered tools, run discovery first:

                from orchestrator.tool_discovery import discover_tools
                catalog = await discover_tools(mcp_client=client, ...)
                planner = LargePlanner(tool_catalog=catalog)

        Phase 3 Usage - Semantic Search:
            When tool_catalog has >20 tools, semantic search automatically selects
            the most relevant 5-10 tools for each request, reducing token usage by 80-90%.

        Phase 4 Usage - Programmatic Tool Calling:
            When enabled, LLM can generate code that orchestrates tool calls in parallel,
            reducing latency by 60-80% and saving 37% additional tokens.
        """
        # Get provider from env if not specified (avoid Optional[str] .lower())
        env_provider = os.getenv("PLANNER_PROVIDER")
        prov = provider if provider is not None else env_provider

        # Default to LiteLLM when available and no explicit provider is set
        if prov is None and LITELLM_AVAILABLE:
            prov = "litellm"
        elif prov is None:
            prov = "openai"

        forced_litellm = os.getenv("PLANNER_FORCE_LITELLM", "0").lower() in ("1", "true", "yes")
        prov_lower = prov.lower()

        # Store original provider before forcing litellm (for provider-specific config)
        self.original_provider = prov_lower

        if forced_litellm and LITELLM_AVAILABLE and prov_lower != "litellm":
            logger.info(f"PLANNER_FORCE_LITELLM enabled; using litellm wrapper for {prov_lower}")
            prov_lower = "litellm"
        self.provider = prov_lower

        # Store tool catalog (will use default if None)
        self.tool_catalog = tool_catalog
        self.use_registry_catalog = use_registry_catalog
        self.registry_catalog_use_cache = registry_catalog_use_cache

        # Phase 3: Semantic search configuration
        self.use_tool_search = use_tool_search
        self.search_threshold = search_threshold
        self.search_engine: Any | None = None  # Lazy init, initialized on first use

        # Phase 4: Programmatic calling configuration
        self.use_programmatic_calling = use_programmatic_calling

        # Session context (optional)
        self.session: ExecutionContext | None = session

        # Declare client type once - will be assigned different client types
        self.client: AsyncAzureOpenAI | AsyncOpenAI | AsyncAnthropic | Any
        self.model: str
        self.raw_model: str | None = None
        self.credential: Any = None

        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI package not installed. Install with: pip install openai")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model or os.getenv("PLANNER_MODEL") or "gpt-4o"

        elif self.provider == "azure-openai":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI package not installed. Install with: pip install openai")

            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
            use_ad = os.getenv("AZURE_OPENAI_USE_AD", "false").lower() == "true"

            if not endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable required")

            use_ad = os.getenv("AZURE_OPENAI_USE_AD", "false").lower() == "true"
            if use_ad:
                # Use Azure AD (Entra ID) authentication
                try:
                    from azure.identity.aio import DefaultAzureCredential

                    self.credential = DefaultAzureCredential()

                    # Token provider must be async and return just the token string
                    async def get_azure_token() -> str:
                        token = await self.credential.get_token(
                            "https://cognitiveservices.azure.com/.default"
                        )
                        return str(token.token)

                    self.client = AsyncAzureOpenAI(
                        azure_ad_token_provider=get_azure_token,
                        azure_endpoint=endpoint,
                        api_version=api_version,
                    )
                    logger.info("Using Azure AD authentication for Azure OpenAI")
                except ImportError as e:
                    raise RuntimeError(
                        "azure-identity package not installed. Install with: pip install azure-identity"
                    ) from e
            else:
                # Use API key authentication
                self.credential = None
                api_key = os.getenv("AZURE_OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "AZURE_OPENAI_API_KEY environment variable required (or set AZURE_OPENAI_USE_AD=true)"
                    )
                self.client = AsyncAzureOpenAI(
                    api_key=api_key, azure_endpoint=endpoint, api_version=api_version
                )
                logger.info("Using API key authentication for Azure OpenAI")
            self.model = model or os.getenv("PLANNER_MODEL") or "gpt-4o"

        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise RuntimeError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = model or os.getenv("PLANNER_MODEL") or "claude-3-5-sonnet-20241022"

        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE or genai is None:
                raise RuntimeError(
                    "Google Gemini package not installed. Install with: pip install google-genai"
                )
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")

            raw_model: str = model or os.getenv("PLANNER_MODEL", "gemini-1.5-pro") or "gemini-1.5-pro"
            resolved_model = _normalize_gemini_model_name(raw_model)
            self.raw_model = raw_model

            # Use google.genai client
            self.client = genai.Client(api_key=api_key)
            self.model = resolved_model

        elif self.provider == "litellm":
            if not LITELLM_AVAILABLE:
                raise RuntimeError(
                    "LiteLLM package not installed. Install with: pip install litellm"
                )
            # litellm handles authentication internally via env vars or per-call kwargs
            self.model = model or os.getenv("PLANNER_MODEL") or "gpt-3.5-turbo"
            # We don't need a client object for litellm as we use module-level functions
            self.client = None

        else:
            raise ValueError(
                f"Unknown provider: {self.provider}. Use 'openai', 'azure-openai', 'anthropic', 'gemini', or 'litellm'"
            )

        logger.info(f"Initialized LargePlanner with {self.provider} ({self.model})")

    async def close(self) -> None:
        """Clean up resources (Azure AD credential, HTTP clients)."""
        if hasattr(self, "client") and self.client is not None:
            close_method = getattr(self.client, "close", None)
            if close_method:
                if asyncio.iscoroutinefunction(close_method):
                    await close_method()
                else:
                    close_method()

        if hasattr(self, "credential") and self.credential is not None:
            await self.credential.close()

    async def __aenter__(self) -> "LargePlanner":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_default_catalog(self) -> ToolCatalog:
        """
        Create default tool catalog with legacy hardcoded tools.
        Provides backward compatibility for existing code.

        Returns:
            ToolCatalog with receipt processing tools
        """
        catalog = ToolCatalog(source="legacy_hardcoded", version="1.0")

        # MCP Tools
        catalog.add_tool(
            ToolDefinition(
                name="receipt_ocr",
                type="mcp",
                description="Extract text from receipt images using OCR",
                parameters=[
                    ToolParameter(
                        name="image_uri",
                        type="string",
                        description="URL or path to receipt image",
                        required=True,
                    )
                ],
                metadata={"output_schema": {"text": "string", "confidence": "float"}},
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="line_item_parser",
                type="mcp",
                description="Parse OCR text into structured line items with prices",
                parameters=[
                    ToolParameter(
                        name="ocr_text",
                        type="string",
                        description="Raw text from receipt",
                        required=True,
                    )
                ],
                metadata={"output_schema": {"items": "array"}},
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="expense_categorizer",
                type="mcp",
                description="Categorize line items into expense categories (food, beverage, etc.)",
                parameters=[
                    ToolParameter(
                        name="items", type="array", description="List of line items", required=True
                    )
                ],
                metadata={"output_schema": {"categorized": "array"}},
            )
        )

        # Function Tools
        catalog.add_tool(
            ToolDefinition(
                name="compute_tax",
                type="function",
                description="Calculate tax amount",
                parameters=[
                    ToolParameter(
                        name="amount", type="number", description="Amount to tax", required=True
                    ),
                    ToolParameter(
                        name="tax_rate", type="number", description="Tax rate (0-1)", required=True
                    ),
                ],
                metadata={"output_type": "float"},
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="merge_items",
                type="function",
                description="Merge items and compute aggregate statistics",
                parameters=[
                    ToolParameter(
                        name="items", type="array", description="List of items", required=True
                    )
                ],
                metadata={
                    "output_schema": {
                        "total_sum": "number",
                        "count": "number",
                        "avg_total": "number",
                    }
                },
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="apply_discount",
                type="function",
                description="Apply percentage discount to amount",
                parameters=[
                    ToolParameter(
                        name="amount", type="number", description="Original amount", required=True
                    ),
                    ToolParameter(
                        name="discount_percent",
                        type="number",
                        description="Discount percentage",
                        required=True,
                    ),
                ],
                metadata={
                    "output_schema": {"original": "number", "discount": "number", "final": "number"}
                },
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="filter_items_by_category",
                type="function",
                description="Filter items by category",
                parameters=[
                    ToolParameter(
                        name="items", type="array", description="List of items", required=True
                    ),
                    ToolParameter(
                        name="category",
                        type="string",
                        description="Category to filter by",
                        required=True,
                    ),
                ],
                metadata={"output_type": "array"},
            )
        )

        catalog.add_tool(
            ToolDefinition(
                name="compute_item_statistics",
                type="function",
                description="Compute comprehensive statistics about items",
                parameters=[
                    ToolParameter(
                        name="items", type="array", description="List of items", required=True
                    )
                ],
                metadata={
                    "output_schema": {
                        "count": "number",
                        "total_amount": "number",
                        "categories": "object",
                    }
                },
            )
        )

        # Code Execution
        catalog.add_tool(
            ToolDefinition(
                name="code_exec",
                type="code_exec",
                description="Execute arbitrary Python code for custom transformations",
                parameters=[
                    ToolParameter(
                        name="code",
                        type="string",
                        description="Python code to execute",
                        required=True,
                    ),
                    ToolParameter(
                        name="input_data",
                        type="object",
                        description="Dict of input variables",
                        required=True,
                    ),
                ],
                metadata={
                    "safety": "Sandboxed execution with safe builtins only",
                    "available_builtins": [
                        "len",
                        "sum",
                        "min",
                        "max",
                        "str",
                        "int",
                        "float",
                        "list",
                        "dict",
                        "range",
                        "sorted",
                        "enumerate",
                        "zip",
                    ],
                    "output_variable": "output",
                },
            )
        )

        return catalog

    def _get_tool_catalog(self, available_tools: list[ToolDefinition] | None = None) -> ToolCatalog:
        """
        Get the tool catalog to use for planning.

        Priority:
        1. available_tools parameter (Phase 3 semantic search results)
        2. self.tool_catalog (injected at init)
        3. Auto-discovered catalog (Phase 2, if auto_discover=True)
        4. Default catalog (legacy hardcoded tools)

        Args:
            available_tools: Optional list of tools from semantic search (Phase 3)

        Returns:
            ToolCatalog instance
        """
        # Phase 3: Use search results if provided
        if available_tools is not None:
            catalog = ToolCatalog(source="semantic_search", version="1.0")
            for tool in available_tools:
                catalog.add_tool(tool)
            return catalog

        # Phase 1: Use injected catalog if provided
        if self.tool_catalog is not None:
            return self.tool_catalog

        # Phase 2: Registry-backed catalog (optional opt-in)
        if self.use_registry_catalog:
            try:
                registry_catalog = get_registry_tool_catalog(
                    use_cache=self.registry_catalog_use_cache
                )
                logger.info(
                    "Using registry catalog: %d tools (cache=%s)",
                    len(registry_catalog.tools),
                    self.registry_catalog_use_cache,
                )
                return registry_catalog
            except Exception as exc:  # Fall back gracefully to default
                logger.info("Registry catalog unavailable, falling back to default catalog: %s", exc)

        # Backward compatibility: Use default catalog
        return self._get_default_catalog()

    def _build_system_prompt(self, available_tools: list[ToolDefinition] | None = None) -> str:
        """
        Build the system prompt for the planner.

        Args:
            available_tools: Optional list of tools from semantic search

        Returns:
            System prompt string with tool definitions in LLM format
        """
        tool_catalog = self._get_tool_catalog(available_tools)

        # Group tools by type for better organization
        tools_by_type = {
            "mcp": tool_catalog.get_by_type("mcp"),
            "function": tool_catalog.get_by_type("function"),
            "code_exec": tool_catalog.get_by_type("code_exec"),
        }

        # Build tool descriptions with flat structure (no type prefixes)
        tool_descriptions = {}
        for tool_type, tools in tools_by_type.items():
            if tools:
                for tool in tools:
                    tool_descriptions[tool.name] = {
                        "type": tool_type,
                        "description": tool.description,
                        "parameters": {p.name: p.type for p in tool.parameters},
                        "required": [p.name for p in tool.parameters if p.required],
                        "metadata": tool.metadata,
                    }

        # Also provide grouped tool names for clarity (used by tests)
        tool_groups = {
            "mcp_tools": [t.name for t in tools_by_type.get("mcp", [])],
            "function_tools": [t.name for t in tools_by_type.get("function", [])],
            "code_exec_tools": [t.name for t in tools_by_type.get("code_exec", [])],
        }

        # Build programmatic calling section if enabled
        ptc_section = ""
        if self.use_programmatic_calling:
            ptc_section = """

PROGRAMMATIC TOOL CALLING (Advanced):

When you need to:
- Call multiple tools in parallel (faster than sequential)
- Filter/transform large datasets before returning to context
- Loop over collections with tool calls
- Apply complex logic (conditionals, aggregations)

Use code_exec with tool orchestration code instead of multiple tool steps:

Example (BAD - Sequential, slow, wastes tokens):
Step 1: get_team_members("engineering") -> 20 members (5KB into context)
Step 2: get_expenses(member1) -> (10KB into context)
Step 3-21: get_expenses(member2-20) -> (200KB+ into context!)
Step 22: Manual comparison in next LLM call

Example (GOOD - Parallel, fast, minimal context):
Step 1: code_exec with:
```python
# All tools are available as async functions
team = await get_team_members(team_id="engineering")
budgets = {{level: await get_budget(level) for level in set(m["level"] for m in team)}}

# Parallel execution (much faster!)
expenses = await asyncio.gather(*[get_expenses(user_id=m["id"], period="Q3") for m in team])

# Filter in code (keeps 200KB out of LLM context!)
exceeded = []
for member, exp in zip(team, expenses):
    total = sum(e["amount"] for e in exp)
    if total > budgets[member["level"]]:
        exceeded.append({{"name": member["name"], "spent": total}})

# Only return summary (2KB vs 200KB!)
print(json.dumps(exceeded))
```

Use programmatic calling when:
[OK] Need to call same tool multiple times (list iteration)
[OK] Can filter/aggregate results before LLM sees them
[OK] Operations are independent (can run in parallel)
[OK] Dealing with large intermediate data

DON'T use programmatic calling when:
[X] Single tool call is sufficient
[X] LLM needs to see full intermediate results
[X] Simple, straightforward workflows
[X] Tools have complex dependencies
"""

        return f"""You are an execution planner for a hybrid orchestration system. Your job is to convert natural language requests into structured JSON execution plans.

Available Tools:
{json.dumps(tool_descriptions, indent=2)}

Tool Groups:
{json.dumps(tool_groups, indent=2)}

Plan Structure:
{{
  "request_id": "unique-id",
  "steps": [
    {{
      "id": "step-1",
      "tool": "tool_name",
      "input": {{"param": "value or step:previous-step"}},
      "depends_on": ["step-id-1", "step-id-2"],
      "mode": "parallel" or "sequential",
      "idempotency_key": "optional-key"
    }}
  ],
  "final_synthesis": {{
    "prompt_template": "Template for final output",
    "meta": {{"expose_inputs_to_reasoner": false}}
  }}
}}

Guidelines:
1. Use step references ("step:step-id") to pass outputs between steps
2. Set dependencies correctly to ensure proper execution order
3. Use "parallel" mode for independent steps, "sequential" for dependent steps
4. Choose the right tool type: MCP for deterministic tasks, functions for structured APIs, code_exec for custom logic
5. Generate valid JSON only, no explanations outside the JSON{ptc_section}

{self._get_response_format_instruction()}"""

    def _get_response_format_instruction(self) -> str:
        """Get the response format instruction based on streaming mode."""
        show_streaming = os.getenv("SHOW_LLM_STREAMING", "false").lower() in ("true", "1", "yes")

        if show_streaming:
            return """
When generating the plan, think through your approach step-by-step:
1. First, analyze the request and identify what needs to be done
2. Check which tools are available and relevant
3. Decide on the execution strategy (parallel vs sequential)
4. Then output the complete JSON plan

Format your response as:
THINKING:
<your reasoning process here>

PLAN:
<the JSON execution plan>"""
        else:
            return "Respond with only the JSON execution plan."

    async def generate_plan(
        self,
        user_request: str,
        context: dict[str, Any] | None = None,
        available_tools: list[ToolDefinition] | None = None,
        session: ExecutionContext | None = None,
    ) -> dict[str, Any]:
        """
        Generate an execution plan from a natural language request.

        Args:
            user_request: Natural language description of what to do
            context: Optional additional context (image URLs, data, etc.)
            available_tools: Optional list of tools from semantic search (Phase 3)

        Returns:
            Dictionary containing the execution plan

        Example:
            # Basic usage (uses default or injected catalog)
            planner = LargePlanner(provider="openai")
            plan = await planner.generate_plan(
                "Process this receipt and calculate the total with tax",
                context={"image_url": "https://..."}
            )

            # With custom tool catalog (Phase 1)
            catalog = ToolCatalog(source="custom")
            planner = LargePlanner(provider="openai", tool_catalog=catalog)
            plan = await planner.generate_plan(...)

            # Phase 3: Semantic search automatically selects relevant tools
            planner = LargePlanner(provider="openai", tool_catalog=large_catalog)
            plan = await planner.generate_plan("send slack message")
            # Automatically searches and uses only relevant tools
        """
        logger.info(f"Generating plan for request: {user_request[:100]}...")

        # Resolve session
        current_context = get_execution_context()
        session_ctx = session or self.session or current_context
        created_session = False
        if session_ctx is None:
            session_ctx = ExecutionContext(task_description=f"Plan generation: {user_request[:80]}")
            created_session = True
        assert session_ctx is not None  # Guarantee for type checker
        if session_ctx.status == "pending":
            session_ctx.mark_started()
        # Set as global for downstream calls
        set_execution_context(session_ctx)

        # Phase 3: Adaptive tool selection with semantic search
        if available_tools is None:
            # Get or create tool catalog
            catalog = self._get_tool_catalog()
            total_tools = len(catalog.tools)

            # Decide whether to use semantic search
            if self.use_tool_search and total_tools > self.search_threshold:
                # Lazy init search engine
                if self.search_engine is None:
                    from orchestrator.tools.tool_search import ToolSearchEngine

                    self.search_engine = ToolSearchEngine()
                    logger.info("Initialized semantic search engine")

                # Search for relevant tools
                search_results = self.search_engine.search(
                    query=user_request,
                    catalog=catalog,
                    top_k=10,  # Get top 10 most relevant tools
                    min_score=0.3,
                )

                available_tools = [tool for tool, score in search_results]

                # Calculate token savings
                tokens_without_search = total_tools * 150  # ~150 tokens per tool
                tokens_with_search = len(available_tools) * 150
                savings_pct = (
                    (tokens_without_search - tokens_with_search) / tokens_without_search
                ) * 100

                logger.info(
                    f"Semantic search: {total_tools} tools -> {len(available_tools)} relevant tools "
                    f"(~{savings_pct:.1f}% token reduction, ~{tokens_without_search - tokens_with_search:,} tokens saved)"
                )
            else:
                # Use all tools (small catalog or search disabled)
                available_tools = list(catalog.tools.values())
                if total_tools <= self.search_threshold:
                    logger.info(f"Using all {total_tools} tools (below search threshold)")
                else:
                    logger.info(f"Using all {total_tools} tools (search disabled)")
        else:
            # Tools explicitly provided (e.g., from external search)
            logger.info(f"Using {len(available_tools)} explicitly provided tools")

        # Build the user message
        user_message = f"User Request: {user_request}\n"
        if context:
            user_message += f"\nContext: {json.dumps(context, indent=2)}"

        try:
            if self.provider in ["openai", "azure-openai"]:
                openai_client = cast(AsyncOpenAI | AsyncAzureOpenAI, self.client)
                response = await openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for consistent planning
                )
                plan_json = response.choices[0].message.content

            elif self.provider == "anthropic":
                anthropic_client = cast(AsyncAnthropic, self.client)
                anthropic_response = await anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self._build_system_prompt(available_tools),
                    messages=[{"role": "user", "content": user_message}],
                    temperature=0.1,
                )
                # response.content[0] can be TextBlock, ToolUseBlock, etc. Only TextBlock has .text
                content_block = cast(Any, anthropic_response).content[0]
                if hasattr(content_block, "text"):
                    plan_json = content_block.text
                else:
                    raise ValueError(f"Expected TextBlock with 'text' attribute, got {type(content_block).__name__}")

            elif self.provider == "gemini":
                prompt = f"{self._build_system_prompt(available_tools)}\n\n{user_message}"
                if GEMINI_AVAILABLE and genai is not None:
                    if self.raw_model is None:
                        raise ValueError("raw_model cannot be None for Gemini provider")
                    candidates = _gemini_model_candidates(self.raw_model)
                    plan_json = ""
                    last_exc: Exception | None = None

                    for candidate in candidates:
                        try:
                            client = cast(Any, self.client)
                            response = await asyncio.to_thread(
                                client.models.generate_content,
                                model=candidate,
                                contents=prompt,
                                config={"temperature": 0.1},
                            )
                            plan_json = getattr(response, "text", "")
                            break
                        except Exception as exc:
                            last_exc = exc
                            logger.warning(
                                "Gemini new SDK generate_content failed for %s: %s", candidate, exc
                            )

                    if not plan_json:
                        import importlib

                        legacy_genai = importlib.import_module("google.generativeai")
                        legacy_genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                        legacy_candidates = [c for c in candidates if not c.startswith("models/")]
                        for candidate in legacy_candidates:
                            try:
                                legacy_model = legacy_genai.GenerativeModel(candidate)
                                response = await legacy_model.generate_content_async(
                                    prompt,
                                    generation_config=legacy_genai.types.GenerationConfig(temperature=0.1),
                                )
                                plan_json = response.text
                                break
                            except Exception as exc:
                                last_exc = exc
                                logger.warning(
                                    "Gemini legacy SDK generate_content failed for %s: %s", candidate, exc
                                )

                    if not plan_json and last_exc:
                        raise last_exc
                else:
                    assert genai is not None
                    client = cast(Any, self.client)
                    response = await client.generate_content_async(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1
                        ),
                    )
                    plan_json = response.text

            elif self.provider == "litellm":
                # LiteLLM wrapper - routes to original provider with its config
                litellm_model = self.model

                # Check if streaming is enabled
                show_streaming = os.getenv("SHOW_LLM_STREAMING", "false").lower() in ("true", "1", "yes")

                litellm_kwargs: dict[str, Any] = {
                    "messages": [
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.1,
                }

                # Only use JSON mode when not streaming (streaming mode allows thinking)
                if not show_streaming:
                    litellm_kwargs["response_format"] = {"type": "json_object"}

                # Route to original provider with its config
                if self.original_provider == "azure-openai":
                    # Azure: Use azure/ prefix to tell LiteLLM this is Azure
                    # and pass api_base for endpoint routing
                    litellm_model = f"azure/{self.model}"
                    litellm_kwargs["api_base"] = os.getenv("AZURE_OPENAI_ENDPOINT")
                    litellm_kwargs["api_key"] = os.getenv("AZURE_OPENAI_API_KEY")
                    litellm_kwargs["api_version"] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
                    logger.info(f"LiteLLM wrapper: {litellm_model} (Azure OpenAI)")

                elif self.original_provider == "openai":
                    # OpenAI: LiteLLM detects from api_key, just pass model name
                    litellm_model = self.model
                    litellm_kwargs["api_key"] = os.getenv("OPENAI_API_KEY")
                    logger.info(f"LiteLLM wrapper: {self.model} (OpenAI)")

                elif self.original_provider == "anthropic":
                    # Anthropic: Use claude model format, pass api_key
                    litellm_model = self.model
                    litellm_kwargs["api_key"] = os.getenv("ANTHROPIC_API_KEY")
                    logger.info(f"LiteLLM wrapper: {self.model} (Anthropic)")

                elif self.original_provider == "gemini":
                    # Gemini: Use google_palm or gemini- prefix
                    litellm_model = self.model
                    if not self.model.startswith("models/"):
                        litellm_model = f"models/{self.model}"
                    litellm_kwargs["api_key"] = os.getenv("GOOGLE_API_KEY")
                    logger.info(f"LiteLLM wrapper: {litellm_model} (Gemini)")
                else:
                    logger.warning(f"LiteLLM wrapper: unknown provider {self.original_provider}, using model as-is")

                if show_streaming:
                    # Stream the response and print in real-time
                    import re
                    litellm_kwargs["stream"] = True
                    response = await litellm.acompletion(model=litellm_model, **litellm_kwargs)
                    plan_json = ""
                    async for chunk in response:
                        if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                print(delta.content, end="", flush=True)
                                plan_json += delta.content
                    print()  # Newline after streaming

                    # Extract JSON from THINKING/PLAN format if present
                    if "PLAN:" in plan_json:
                        plan_json = plan_json.split("PLAN:", 1)[1].strip()

                    # Remove markdown code blocks if present
                    plan_json = re.sub(r'^```json\s*', '', plan_json, flags=re.MULTILINE)
                    plan_json = re.sub(r'\s*```\s*$', '', plan_json, flags=re.MULTILINE)
                    plan_json = plan_json.strip()
                else:
                    # Non-streaming mode (original behavior)
                    response = await litellm.acompletion(model=litellm_model, **litellm_kwargs)
                    plan_json = response.choices[0].message.content

            # Parse and validate JSON
            if not plan_json:
                raise ValueError("Failed to generate plan: empty response from LLM provider")
            plan = cast(dict[str, Any], json.loads(plan_json))
            # Attach request_id for downstream correlation
            plan.setdefault("request_id", session_ctx.request_id)

            session_ctx.add_metadata(
                "plan_generation_result",
                {
                    "steps": len(plan.get("steps", [])),
                    "provider": self.provider,
                    "model": self.model,
                },
            )
            session_ctx.mark_completed(result={"plan": plan})
            logger.info(f"Generated plan with {len(plan.get('steps', []))} steps")

            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {e}", exc_info=True)
            session_ctx.mark_failed(error=str(e))
            raise RuntimeError(f"Failed to generate execution plan: {e}") from e
        finally:
            if created_session:
                # Clear global context if we created it
                set_execution_context(current_context)
            else:
                # Restore previous context
                set_execution_context(current_context)

    async def refine_plan(
        self,
        original_plan: dict[str, Any],
        feedback: str,
        available_tools: list[ToolDefinition] | None = None,
        session: ExecutionContext | None = None,
    ) -> dict[str, Any]:
        """
        Refine an existing plan based on feedback or errors.

        Args:
            original_plan: The original execution plan
            feedback: Description of issues or desired changes
            available_tools: Optional list of tools from semantic search (Phase 3)

        Returns:
            Updated execution plan
        """
        logger.info(f"Refining plan based on feedback: {feedback[:100]}...")

        # Resolve session
        current_context = get_execution_context()
        session_ctx = session or self.session or current_context
        created_session = False
        if session_ctx is None:
            session_ctx = ExecutionContext(task_description="Plan refinement")
            created_session = True
        assert session_ctx is not None  # Guarantee for type checker
        if session_ctx.status == "pending":
            session_ctx.mark_started()
        set_execution_context(session_ctx)

        user_message = f"""Original Plan:
{json.dumps(original_plan, indent=2)}

Feedback/Issues:
{feedback}

Please generate an improved plan that addresses the feedback."""

        try:
            if self.provider in ["openai", "azure-openai"]:
                openai_client = cast(AsyncOpenAI | AsyncAzureOpenAI, self.client)
                response = await openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                plan_json = response.choices[0].message.content

            elif self.provider == "anthropic":
                anthropic_client = cast(AsyncAnthropic, self.client)
                anthropic_response = await anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=self._build_system_prompt(available_tools),
                    messages=[{"role": "user", "content": user_message}],
                    temperature=0.1,
                )
                content_block = cast(Any, anthropic_response).content[0]
                if hasattr(content_block, "text"):
                    plan_json = content_block.text
                else:
                    raise ValueError(
                        f"Expected TextBlock with 'text' attribute, got {type(content_block).__name__}"
                    )

            elif self.provider == "gemini":
                prompt = f"{self._build_system_prompt(available_tools)}\n\n{user_message}"
                if GEMINI_AVAILABLE and genai is not None:
                    if self.raw_model is None:
                        raise ValueError("raw_model cannot be None for Gemini provider")
                    candidates = _gemini_model_candidates(self.raw_model)
                    plan_json = ""
                    last_exc: Exception | None = None

                    for candidate in candidates:
                        try:
                            client = cast(Any, self.client)
                            response = await asyncio.to_thread(
                                client.models.generate_content,
                                model=candidate,
                                contents=prompt,
                                config={"temperature": 0.1},
                            )
                            plan_json = getattr(response, "text", "")
                            break
                        except Exception as exc:
                            last_exc = exc
                            logger.warning(
                                "Gemini new SDK generate_content failed for %s: %s", candidate, exc
                            )

                    if not plan_json:
                        import importlib

                        legacy_genai = importlib.import_module("google.generativeai")
                        legacy_genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                        legacy_candidates = [c for c in candidates if not c.startswith("models/")]
                        for candidate in legacy_candidates:
                            try:
                                legacy_model = legacy_genai.GenerativeModel(candidate)
                                response = await legacy_model.generate_content_async(
                                    prompt,
                                    generation_config=legacy_genai.types.GenerationConfig(temperature=0.1),
                                )
                                plan_json = response.text
                                break
                            except Exception as exc:
                                last_exc = exc
                                logger.warning(
                                    "Gemini legacy SDK generate_content failed for %s: %s", candidate, exc
                                )

                    if not plan_json and last_exc:
                        raise last_exc
                else:
                    assert genai is not None
                    client = cast(Any, self.client)
                    response = await client.generate_content_async(
                        prompt,
                        generation_config=genai.types.GenerationConfig(temperature=0.1),
                    )
                    plan_json = response.text

            elif self.provider == "litellm":
                response = await litellm.acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt(available_tools)},
                        {"role": "user", "content": user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                plan_json = response.choices[0].message.content

            if not plan_json:
                raise ValueError("Failed to refine plan: empty response from LLM provider")
            refined_plan = cast(dict[str, Any], json.loads(plan_json))
            refined_plan.setdefault("request_id", session_ctx.request_id)
            session_ctx.add_metadata(
                "plan_refinement_result",
                {
                    "steps": len(refined_plan.get("steps", [])),
                    "provider": self.provider,
                    "model": self.model,
                },
            )
            session_ctx.mark_completed(result={"plan": refined_plan})
            logger.info("Plan refinement completed")

            return refined_plan
        except Exception as e:
            logger.error(f"Plan refinement failed: {e}", exc_info=True)
            session_ctx.mark_failed(error=str(e))
            raise RuntimeError(f"Failed to refine execution plan: {e}") from e
        finally:
            if created_session:
                set_execution_context(current_context)
            else:
                set_execution_context(current_context)

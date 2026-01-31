# ToolWeaver

**Package-first tool orchestration for Python.**

ToolWeaver brings together **Model Context Protocol (MCP)** for tools and the **Agent2Agent (A2A) Protocol** for interoperability. It treats LLMs as planners, not workers, enabling verifiable, cost-effective workflows that scale from prototypes to production.

[![PyPI version](https://badge.fury.io/py/toolweaver.svg)](https://pypi.org/project/toolweaver/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/ushakrishnan/ToolWeaver/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-964%20passing%20(98.5%25)-brightgreen.svg)](https://github.com/ushakrishnan/ToolWeaver/actions)
[![Ruff](https://img.shields.io/badge/ruff-pass-brightgreen.svg)](https://docs.astral.sh/ruff/)

---

## The Big Idea

Most AI agents today work through constant back-and-forth: you send a message, they try one thing, report back, you send another message. This is slow, expensive, and prone to drift.

**ToolWeaver inverts this model.** The LLM is the *planner*, not the *worker*. 

1.  **You ask**: "Process these 100 receipts and categorize by vendor."
2.  **LLM plans**: Discovers available tools (MCP, A2A, custom), writes a detailed execution plan.
3.  **System executes**: Deterministic runtime executes the plan—no LLM in the loop, no token waste.

**Result**: 80-95% cost reduction, verifiable execution, human-inspectable plans.

---

## Technical Deep Dive

### Planner-Executor Architecture

**O(1) LLM calls**, regardless of workflow complexity:
- **Planning**: LLM generates execution plan (1-2 calls)
- **Execution**: Deterministic runtime with no LLM overhead
- **Synthesis**: LLM consolidates results (1 call)

**Benefits**:
- Eliminate retry loops and hallucinations
- Human-inspectable plans (audit before execution)
- Suspend/resume for long-running workflows

### Model Context Protocol (MCP)

First-class MCP integration for tool interoperability:
- **Auto-discovery**: Introspect MCP servers and expose tools to planner
- **Stateless execution**: Tools run in isolation, no context pollution
- **Standard compliance**: Works with any MCP-compatible server

### Agent2Agent (A2A) Protocol

Production-grade A2A support for agent-to-agent communication:
- **JSON-RPC 2.0**: Standard protocol over HTTP/S
- **Interoperability**: Connect with external agents (LangChain, AutoGen, custom)
- **Enterprise-ready**: Circuit breakers, retry logic, idempotency keys

### Stdlib Tools & Extensibility

Built-in tools for common workflows:
- **web_search**: DuckDuckGo search (privacy-focused, no API key)
- **web_fetch**: HTTP content retrieval with domain allowlists
- **memory**: Key-value storage (file/Redis backends)
- **tool_search**: Dynamic tool discovery
- **Custom tools**: Extend with `@mcp_tool` decorator + RLM hooks

**RLM Framework** (Recursive Language Models):
- Pre-call validation (token limits, input sanitization)
- Post-call truncation (output capping, credential redaction)
- Token budgets for cost control

### Multi-Provider Support

Works with 100+ LLM providers via LiteLLM:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet/Haiku)
- Azure OpenAI
- AWS Bedrock
- Google Vertex AI
- Local models (Ollama, vLLM)

Switch providers without changing code—just update `.env`.

### LLM Streaming & Real-Time Feedback

See the LLM's "thinking process" in real-time—like GitHub Copilot's reasoning display:

```bash
# Enable streaming in .env
SHOW_LLM_STREAMING=true
```

**What you'll see**:
1. **THINKING**: LLM's reasoning process ("The request is straightforward...")
2. **PLAN**: Structured execution plan (JSON)
3. **SYNTHESIS**: Final one-liner answer

Perfect for building chat UIs, dashboards, or debugging agent decisions. The `weather_api_demo_capture.py` sample shows how to capture and format streaming output for UI rendering with collapsible thinking sections.

---

## Architect's Corner

### Prototype-to-Production Path

**Unit Economics**: Shift compute from GPU (LLM) to CPU (runtime)
- **Planning**: 1-2 calls with large model ($0.01-0.05)
- **Execution**: 0 LLM calls, pure Python runtime ($0.00)
- **Synthesis**: 1 call with large model ($0.01-0.05)
- **Hybrid optimization**: Use small models for execution (Haiku, GPT-3.5) = 85-95% savings

**Observability & Governance**:
- **White-box execution**: Plans are inspectable *before* execution
- **Audit trails**: Every tool call logged with inputs/outputs/metadata
- **Policy enforcement**: Inject middleware for approval gates, rate limits, compliance
- **Receipts**: JSON artifacts for debugging and compliance

**Vendor Neutrality**:
- **Multi-provider**: Switch between OpenAI, Anthropic, Azure, Bedrock without code changes
- **Fallback strategies**: Automatic failover to backup providers
- **Cost optimization**: Route to cheapest provider per task

**Separation of Concerns**:
- **Developers**: Build stateless tools with `@mcp_tool`
- **Prompt engineers**: Tune planner selection logic
- **Ops teams**: Manage registry, observability, caching
- **Security**: Sandboxing, domain allowlists, token budgets

**Enterprise Features**:
- **Offline mode**: Air-gapped deployments with domain allowlists
- **Feature flips**: Granular control over enabled tools (.env)
- **Redis caching**: Distributed cache for high-volume workloads
- **Grafana/Prometheus**: Built-in monitoring integration
- **Skills packaging**: Distribute tool bundles as pip packages

---

## Features at a Glance

- **34 Running Samples**: From fundamentals to production patterns (receipt processing, multi-agent, API servers, caching, observability)
- **Hybrid Model Routing**: Large models plan, small models execute—80-95% cost savings
- **Stdlib Tools**: Built-in web_search, web_fetch, memory, tool_search with RLM safeguards
- **MCP + A2A Support**: First-class integration with both protocols
- **Multi-Provider**: OpenAI, Anthropic, Azure, Bedrock, Vertex AI, local models
- **Production Ready**: Monitoring, logging, sandboxing, caching, offline mode
- **Type-Safe**: Pydantic validation, JSON Schema auto-generation
- **Extensible**: Add custom tools with `@mcp_tool`, load external agents via A2A

---

## Installation

```bash
pip install toolweaver
```

Optional extras:

```bash
pip install toolweaver[azure]       # Add Azure AI services
pip install toolweaver[openai]      # Add OpenAI
pip install toolweaver[anthropic]   # Add Anthropic/Claude
pip install toolweaver[redis]       # Add Redis-backed tool registry
pip install toolweaver[all]         # All extras
```

Registry backends (env-driven):
- Default: in-memory local registry (no extra install)
- SQLite: `ORCHESTRATOR_TOOL_REGISTRY=sqlite` (uses stdlib, no extra install; optional `ORCHESTRATOR_TOOL_DB=.toolweaver/tools.db`)
- Redis: `ORCHESTRATOR_TOOL_REGISTRY=redis` (requires `toolweaver[redis]`; optional `ORCHESTRATOR_REDIS_URL`, `ORCHESTRATOR_REDIS_NAMESPACE`)

### For Contributors (Development Setup)

```bash
git clone https://github.com/ushakrishnan/ToolWeaver.git
cd ToolWeaver
python -m venv .venv
# Activate venv (Windows: .venv\Scripts\activate, Linux/Mac: source .venv/bin/activate)
pip install -e ".[dev]"
```

---

## Quick Start

Create a simple tool and let ToolWeaver orchestrate:

```python
from orchestrator import LargePlanner, mcp_tool
import asyncio

@mcp_tool(description="Calculate string length")
async def get_length(text: str) -> int:
    return len(text)

async def main():
    planner = LargePlanner(provider="anthropic", model="claude-3-5-sonnet-20241022")
    result = await planner.ask("What is the length of 'Hello ToolWeaver'?")
    print(result)

asyncio.run(main())
```

**Next**: Explore [34 samples](https://ushakrishnan.github.io/ToolWeaver/samples/) from basics to production.

---

## Documentation

**[Official Documentation](https://ushakrishnan.github.io/ToolWeaver/)** | **[Samples Library (34)](https://ushakrishnan.github.io/ToolWeaver/samples/)**

- **[Get Started](https://ushakrishnan.github.io/ToolWeaver/get-started/quickstart/)**
- **[Architecture](https://ushakrishnan.github.io/ToolWeaver/architecture/)**
- **[Tutorials](https://ushakrishnan.github.io/ToolWeaver/tutorials/)** (Adding Tools, Model Providers, Data Pipelines, RLM)
- **[Cookbook](https://ushakrishnan.github.io/ToolWeaver/how-to/cookbook/)** (8 Common Patterns)
- **[Contributing](https://github.com/ushakrishnan/ToolWeaver/blob/main/CONTRIBUTING.md)**

### Sample Categories (34 Total)

- **Fundamentals** (6): Receipt processing, GitHub, RAG, custom tools, model providers
- **Patterns** (9): Workflows, planning, error recovery, fetch-analyze-store, control flow
- **Architecture** (8): Multi-agent, hybrid routing, API servers, sandboxing
- **Production** (5): Caching, observability, dashboard, skills, interactive chat
- **Integrations** (5): MCP client/server, plugins, agent-to-agent (A2A), **LLM streaming demos**
- **Tooling** (2): Custom tools, stdlib demo (with offline variant)

---

## Stdlib Tool Configuration

Control built-in tools, logging, and LLM streaming via `.env`:

```bash
# ============================================================
# LOGGING CONFIGURATION
# ============================================================
LOG_LEVEL=ERROR                          # Global logging level
TOOLWEAVER_LOG_LEVEL=INFO                # Package-specific override
SILENT_MODE=false                        # Suppress all logging infrastructure
LITELLM_LOG_LEVEL=WARNING                # External library logging

# ============================================================
# LLM STREAMING (Show Model's Thinking Process)
# ============================================================
SHOW_LLM_STREAMING=false                 # Enable to see LLM reasoning in real-time
                                         # Shows: THINKING → PLAN → SYNTHESIS
                                         # Useful for: Debugging, UI rendering, demos

# ============================================================
# STDLIB TOOLS
# ============================================================
TOOLWEAVER_STDLIB_ENABLED=web_search,web_fetch,memory,tool_search
TOOLWEAVER_STDLIB_WEB_FETCH_DOMAIN_ALLOWLIST=example.com,trusted.org
```

**Logging Precedence**: SILENT_MODE → TOOLWEAVER_LOG_LEVEL → LOG_LEVEL → Default (INFO)

**Streaming Output**:
- `SHOW_LLM_STREAMING=true` enables real-time LLM output during planning and synthesis
- Perfect for chat UIs: Think phase (collapsible), Plan (JSON), Synthesis (one-liner)
- See `weather_api_demo_streaming.py` and `weather_api_demo_capture.py` samples

---

## Provider Dependencies

ToolWeaver supports multiple LLM providers. Some samples use Anthropic Claude; others demonstrate OpenAI, Azure, or local models.

**API Keys**: Set environment variables for your chosen provider:
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
AZURE_API_KEY=your_key_here
```

**Licensing**: ToolWeaver is Apache 2.0. Provider SDKs (Claude, OpenAI) have their own terms:
- **ToolWeaver**: Licensed under Apache License 2.0
- **Claude SDK**: Anthropic's [Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms)
- **OpenAI SDK**: OpenAI's [Terms of Use](https://openai.com/policies/terms-of-use)
- Users are responsible for obtaining API keys and complying with provider terms

See [NOTICE](./NOTICE) and [Licensing Guide](./docs/legal/licensing-and-compliance.md) for complete details.

**Testing**: Use dummy keys for local testing—no real API calls without valid credentials.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/CONTRIBUTING.md) for guidelines.

**Quality Gates**:
- Ruff linting (0 errors)
- Mypy type checking (0 errors)
- Pytest (964 tests, 98.5% pass rate)
- All samples runnable

---

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

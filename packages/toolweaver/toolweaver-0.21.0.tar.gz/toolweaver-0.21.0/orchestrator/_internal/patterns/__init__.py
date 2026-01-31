"""Pluggable Architecture Patterns

This module provides abstract base classes for the 7 core pluggable systems:
1. StorageBackend - Persistent storage (files, databases, cloud)
2. ProfileLoader - Configuration/profile management
3. ToolRegistry - Tool discovery and registration
4. LLMProvider - Language model integration
5. InstrumentLoader - Workflow/instrument templates
6. ObservabilityBackend - Observability and monitoring
7. AuthProvider - Authentication and authorization

Each pattern consists of:
- Abstract interface (base.py) - defines contract
- Concrete implementations - storage/, profiles/, tools/, llm/, instruments/, observability/, auth/
- Factory function - auto-discovery based on env vars
"""

__all__ = []

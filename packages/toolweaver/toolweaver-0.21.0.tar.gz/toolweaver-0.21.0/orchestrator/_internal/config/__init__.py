"""Configuration Module

Centralized configuration management:
- paths.py - AppPaths for environment-aware path management
- settings.py - Global configuration (future)
- defaults.py - Default values (future)
- schemas.py - Configuration schemas (future)
"""

from orchestrator._internal.config.paths import AppPaths

__all__ = ["AppPaths"]

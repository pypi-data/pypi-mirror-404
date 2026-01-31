"""
Environment loader for ToolWeaver.

This module must be imported FIRST, before any other orchestrator modules,
to ensure .env is loaded from the repository root.

This is imported automatically by conftest.py and orchestrator/__init__.py,
but can also be imported explicitly to ensure .env is loaded early.
"""

from pathlib import Path

try:
    from dotenv import load_dotenv

    # Find the repository root by looking for .env
    # Start from this file's directory and go up
    current = Path(__file__).parent
    while current != current.parent:
        env_file = current.parent / ".env"
        if env_file.exists():
            # Load .env but don't override existing environment variables
            # This allows command-line env vars to take precedence
            load_dotenv(env_file, override=False)
            # Debug: Print which .env was loaded (uncomment for troubleshooting)
            # print(f"[DEBUG] Loaded .env from: {env_file}", file=sys.stderr)
            break
        current = current.parent
except ImportError:
    # dotenv not available, environment variables must be set manually
    pass

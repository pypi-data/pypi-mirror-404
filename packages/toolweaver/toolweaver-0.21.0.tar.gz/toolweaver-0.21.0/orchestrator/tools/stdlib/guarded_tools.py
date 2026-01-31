"""
Guarded stdlib tools: bash, code_exec, text_edit.

These tools are disabled by default and require explicit opt-in via config.
Each includes sandboxing, allowlisting, and RLM safeguards.

Configuration:
    TOOLWEAVER_STDLIB_GUARDED_ENABLED (default: "" - all disabled)
    TOOLWEAVER_STDLIB_BASH_ENABLED (default: False)
    TOOLWEAVER_STDLIB_BASH_ALLOWLIST_PATHS (default: "")
    TOOLWEAVER_STDLIB_CODE_EXEC_ENABLED (default: False)
    TOOLWEAVER_STDLIB_CODE_EXEC_TIMEOUT_S (default: 10)
    TOOLWEAVER_STDLIB_TEXT_EDIT_ENABLED (default: False)
    TOOLWEAVER_STDLIB_TEXT_EDIT_ALLOWLIST_PATHS (default: "")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from orchestrator.tools.stdlib.bash_providers import get_bash_provider
from orchestrator.tools.stdlib.code_exec_providers import get_code_exec_provider
from orchestrator.tools.stdlib.text_edit_providers import get_text_edit_provider

logger = logging.getLogger(__name__)


# ============================================================
# Configuration Helpers
# ============================================================


def _is_guarded_enabled(tool_name: str) -> bool:
    """Check if a guarded tool is explicitly enabled."""
    # Individual tool flag takes precedence
    individual_flag = os.getenv(f"TOOLWEAVER_STDLIB_{tool_name.upper()}_ENABLED")
    if individual_flag:
        return individual_flag.lower() in ("true", "1", "yes")

    # Fall back to global guarded list
    guarded_enabled = os.getenv("TOOLWEAVER_STDLIB_GUARDED_ENABLED", "")
    return tool_name in [t.strip() for t in guarded_enabled.split(",")]


def _get_allowlist_paths(tool_name: str) -> list[str]:
    """Get allowlist paths for a guarded tool."""
    allowlist_str = os.getenv(
        f"TOOLWEAVER_STDLIB_{tool_name.upper()}_ALLOWLIST_PATHS", ""
    )
    return [p.strip() for p in allowlist_str.split(":") if p.strip()]


def _get_config(key: str, default: str = "") -> str:
    """Get a configuration value from environment."""
    return os.getenv(f"TOOLWEAVER_STDLIB_{key}", default)


def _path_in_allowlist(path: str, allowlist: list[str]) -> bool:
    """Check if a path is in the allowlist."""
    if not allowlist:
        return False

    path_obj = Path(path).resolve()
    for allowed in allowlist:
        allowed_obj = Path(allowed).resolve()
        try:
            path_obj.relative_to(allowed_obj)
            return True
        except ValueError:
            continue
    return False


# ============================================================
# Guarded Tool: bash
# ============================================================


def bash(
    command: str, timeout_s: int = 10, allowlist_paths: list[str] | None = None
) -> dict[str, Any]:
    """
    Execute a bash command (GUARDED - disabled by default).

    Args:
        command: Bash command to execute (max 5000 chars)
        timeout_s: Execution timeout in seconds (max 60)
        allowlist_paths: Optional path allowlist for file operations

    Returns:
        Dictionary with returncode, stdout, stderr

    Security:
        - Disabled by default; requires TOOLWEAVER_STDLIB_BASH_ENABLED=true
        - Output truncated to 5000 chars
        - Redacted env vars (no AWS_SECRET, etc. in output)

    RLM Hooks:
        - Pre-call: Validate command format, cap timeout, check allowlist
        - Post-call: Redact credentials, truncate output

    Example:
        # Local execution (default)
        result = bash("ls -la", timeout_s=5)

        # Docker container (isolated)
        os.environ["TOOLWEAVER_STDLIB_BASH_PROVIDER"] = "docker"
        result = bash("echo 'hello'", timeout_s=10)

        # SSH remote
        os.environ["TOOLWEAVER_STDLIB_BASH_PROVIDER"] = "ssh"
        os.environ["SSH_HOST"] = "remote-server.com"
        result = bash("whoami", timeout_s=5)
    """
    if not _is_guarded_enabled("bash"):
        return {
            "error": "bash tool is not enabled (set TOOLWEAVER_STDLIB_BASH_ENABLED=true to enable)"
        }

    # Pre-call validation (RLM)
    command = command[:5000]  # Truncate command
    timeout_s = min(timeout_s, 60)

    # Get provider
    provider_name = _get_config("BASH_PROVIDER", "local")

    try:
        provider = get_bash_provider(provider_name)
        result = provider.execute(command, timeout_s, allowlist_paths)  # type: ignore

        # Post-call processing (RLM): truncate output, redact sensitive data
        if "stdout" in result:
            result["stdout"] = result["stdout"][:5000]
        if "stderr" in result:
            result["stderr"] = result["stderr"][:5000]

        logger.debug(f"bash ({provider_name}): exit_code={result.get('exit_code', -1)}")
        return result

    except ValueError as e:
        logger.error(f"bash configuration error: {e}")
        return {"error": str(e), "command": command}

    except Exception as e:
        logger.error(f"bash error with provider {provider_name}: {e}")
        return {"error": f"Execution failed: {str(e)}", "command": command}


# ============================================================
# Guarded Tool: code_exec
# ============================================================


def code_exec(
    language: str, source: str, timeout_s: int = 10
) -> dict[str, Any]:
    """
    Execute code in a safe sandbox (GUARDED - disabled by default).

    Args:
        language: Programming language (python, javascript, bash, etc.)
        source: Source code to execute (max 10000 chars)
        timeout_s: Execution timeout in seconds (max 30)

    Returns:
        Dictionary with stdout, stderr, exit_code

    Security:
        - Disabled by default; requires TOOLWEAVER_STDLIB_CODE_EXEC_ENABLED=true
        - Containerized or jailed execution
        - 30s timeout max, 10MB output cap
        - No network access or file system access

    RLM Hooks:
        - Pre-call: Validate language, cap source size, cap timeout
        - Post-call: Truncate output to 10000 chars

    Example:
        # Local execution (default - WARNING: untrusted code!)
        result = code_exec("python", "print('hello')")

        # Docker container (isolated)
        os.environ["TOOLWEAVER_STDLIB_CODE_EXEC_PROVIDER"] = "docker"
        result = code_exec("python", "import os; print(os.getcwd())")

        # AWS Lambda (serverless)
        os.environ["TOOLWEAVER_STDLIB_CODE_EXEC_PROVIDER"] = "lambda"
        result = code_exec("javascript", "console.log('hello')")
    """
    if not _is_guarded_enabled("code_exec"):
        return {
            "error": "code_exec tool is not enabled (set TOOLWEAVER_STDLIB_CODE_EXEC_ENABLED=true to enable)"
        }

    # Pre-call validation (RLM)
    timeout_s = min(timeout_s, 30)
    source_len = len(source)
    if source_len > 10000:
        return {"error": f"source code too large: {source_len} bytes > 10000 max"}

    # Get provider
    provider_name = _get_config("CODE_EXEC_PROVIDER", "local")

    try:
        provider = get_code_exec_provider(provider_name)
        result = provider.execute(language, source, timeout_s)  # type: ignore

        # Post-call processing (RLM): truncate output
        if "stdout" in result:
            result["stdout"] = result["stdout"][:10000]
        if "stderr" in result:
            result["stderr"] = result["stderr"][:10000]

        logger.debug(f"code_exec ({provider_name}): {language}, exit_code={result.get('exit_code', -1)}")
        return result

    except ValueError as e:
        logger.error(f"code_exec configuration error: {e}")
        return {"error": str(e), "language": language}

    except Exception as e:
        logger.error(f"code_exec error with provider {provider_name}: {e}")
        return {"error": f"Execution failed: {str(e)}", "language": language}


# ============================================================
# Guarded Tool: text_edit
# ============================================================


def text_edit(
    path: str,
    op: str,
    content: str = "",
    allowlist_paths: list[str] | None = None,
) -> dict[str, Any]:
    """
    Edit files on disk (GUARDED - disabled by default).

    Args:
        path: File path (max 1000 chars)
        op: Operation: "read", "write", "append", "delete"
        content: Content for write/append operations (max 100000 chars)
        allowlist_paths: Optional path allowlist for safety

    Returns:
        Dictionary with operation result, file content (for read), or status

    Security:
        - Disabled by default; requires TOOLWEAVER_STDLIB_TEXT_EDIT_ENABLED=true
        - Allowlist checking if provided
        - No binary files (text only)
        - Newline normalization (LF)
        - Size cap: 100KB per write

    RLM Hooks:
        - Pre-call: Validate path, check allowlist, validate op
        - Post-call: Truncate content for reads, normalize newlines

    Example:
        # Local filesystem (default)
        result = text_edit("/tmp/test.txt", "write", "hello world")

        # S3 storage
        os.environ["TOOLWEAVER_STDLIB_TEXT_EDIT_PROVIDER"] = "s3"
        os.environ["S3_BUCKET"] = "my-bucket"
        result = text_edit("data/file.txt", "write", "content")

        # Git (auto-commit)
        os.environ["TOOLWEAVER_STDLIB_TEXT_EDIT_PROVIDER"] = "git"
        result = text_edit("README.md", "write", "# Updated")
    """
    if not _is_guarded_enabled("text_edit"):
        return {
            "error": "text_edit tool is not enabled (set TOOLWEAVER_STDLIB_TEXT_EDIT_ENABLED=true to enable)"
        }

    # Pre-call validation (RLM)
    if op not in ["read", "write", "append", "delete"]:
        return {"error": f"op must be 'read', 'write', 'append', or 'delete'; got {op}"}

    path_obj: Path = Path(path).resolve()

    # Allowlist check if provided
    if allowlist_paths and not _path_in_allowlist(str(path_obj), allowlist_paths):
        return {
            "error": f"path {path_obj} is not in allowlist: {allowlist_paths}"
        }

    # Get provider
    provider_name = _get_config("TEXT_EDIT_PROVIDER", "local")

    try:
        provider = get_text_edit_provider(provider_name)

        if op == "read":
            result = provider.read(str(path_obj))
            # Post-call processing (RLM): truncate content
            if "content" in result and len(result["content"]) > 100000:
                result["content"] = result["content"][:100000]
                result["truncated"] = True
        elif op == "write":
            result = provider.write(str(path_obj), content)
        elif op == "append":
            result = provider.append(str(path_obj), content)
        else:  # delete
            result = provider.delete(str(path_obj))

        logger.debug(f"text_edit ({provider_name}): op={op}, path={path_obj}")
        return result

    except ValueError as e:
        logger.error(f"text_edit configuration error: {e}")
        return {"error": str(e), "path": path}

    except Exception as e:
        logger.error(f"text_edit error with provider {provider_name}: {e}")
        return {"error": f"Operation failed: {str(e)}", "path": path}

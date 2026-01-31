"""
Code execution provider adapters for stdlib code_exec (guarded) tool.

This module provides a unified interface for different code execution backends
(local process, Docker container, serverless, sandboxed API, etc.).

Users can add custom providers by:
1. Subclassing CodeExecProvider
2. Implementing the execute() method
3. Registering with register_code_exec_provider()

Example custom provider:
    class LambdaProvider(CodeExecProvider):
        def execute(self, language: str, source: str, timeout_s: int) -> dict:
            # Invoke AWS Lambda with code
            response = lambda_client.invoke(
                FunctionName="code-executor",
                Payload=json.dumps({"language": language, "source": source}),
            )
            return json.loads(response["Payload"].read())

    register_code_exec_provider("lambda", LambdaProvider)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available code exec providers
_CODE_EXEC_PROVIDERS: dict[str, type[CodeExecProvider]] = {}


# ============================================================
# Base Code Exec Provider Interface
# ============================================================


class CodeExecProvider(ABC):
    """
    Base class for code execution providers.

    Subclass this to add support for different execution environments
    (Docker, Lambda, sandboxed APIs, etc.).
    """

    @abstractmethod
    def execute(self, language: str, source: str, timeout_s: int) -> dict[str, Any]:
        """
        Execute code in the specified language.

        Args:
            language: Programming language (python, javascript, bash, etc.)
            source: Source code to execute (already validated)
            timeout_s: Timeout in seconds (already capped)

        Returns:
            Dictionary containing:
            - stdout (str): Standard output
            - stderr (str): Standard error
            - exit_code (int): Exit code (0 = success)
            - language (str): Language used
            - truncated (bool, optional): Whether output was truncated

        Raises:
            Exception: If execution fails (caught by caller)
        """
        pass


# ============================================================
# Local Executor Provider (Default)
# ============================================================


class LocalExecutorProvider(CodeExecProvider):
    """
    Execute code in local subprocess.

    WARNING: This executes untrusted code locally! Use only in controlled environments.
    Consider using Docker or sandboxed providers for production.
    """

    LANGUAGE_COMMANDS = {
        "python": ["python", "-c"],
        "python3": ["python3", "-c"],
        "javascript": ["node", "-e"],
        "node": ["node", "-e"],
        "bash": ["bash", "-c"],
        "sh": ["sh", "-c"],
        "ruby": ["ruby", "-e"],
        "perl": ["perl", "-e"],
    }

    def execute(self, language: str, source: str, timeout_s: int) -> dict[str, Any]:
        language_lower = language.lower()

        if language_lower not in self.LANGUAGE_COMMANDS:
            return {
                "stdout": "",
                "stderr": f"Unsupported language: {language}. Supported: {', '.join(self.LANGUAGE_COMMANDS.keys())}",
                "exit_code": 1,
                "language": language,
            }

        cmd = self.LANGUAGE_COMMANDS[language_lower] + [source]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "language": language,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_s}s",
                "exit_code": 124,  # Standard timeout exit code
                "language": language,
            }


# ============================================================
# Docker Executor Provider
# ============================================================


class DockerExecutorProvider(CodeExecProvider):
    """
    Execute code in isolated Docker container.

    Provides better security than local execution by running in isolated container.
    Requires: Docker installed and running
    Configure with: DOCKER_EXEC_IMAGE (default: python:3.11-slim)
    """

    LANGUAGE_IMAGES = {
        "python": "python:3.11-slim",
        "python3": "python:3.11-slim",
        "javascript": "node:20-slim",
        "node": "node:20-slim",
        "bash": "ubuntu:22.04",
        "sh": "alpine:latest",
        "ruby": "ruby:3.2-slim",
    }

    def execute(self, language: str, source: str, timeout_s: int) -> dict[str, Any]:
        language_lower = language.lower()

        if language_lower not in self.LANGUAGE_IMAGES:
            return {
                "stdout": "",
                "stderr": f"Unsupported language: {language}",
                "exit_code": 1,
                "language": language,
            }

        image = os.getenv("DOCKER_EXEC_IMAGE", self.LANGUAGE_IMAGES[language_lower])

        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".code", delete=False) as f:
            f.write(source)
            code_file = f.name

        try:
            # Execute in Docker container
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{code_file}:/code",
                "--network", "none",  # No network access
                "--memory", "512m",  # Memory limit
                "--cpus", "1",  # CPU limit
                image,
            ]

            # Add language-specific execution command
            if language_lower in ("python", "python3"):
                cmd += ["python", "/code"]
            elif language_lower in ("javascript", "node"):
                cmd += ["node", "/code"]
            elif language_lower in ("bash", "sh"):
                cmd += [language_lower, "/code"]
            elif language_lower == "ruby":
                cmd += ["ruby", "/code"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "language": language,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_s}s",
                "exit_code": 124,
                "language": language,
            }

        finally:
            # Clean up temp file
            Path(code_file).unlink(missing_ok=True)


# ============================================================
# Lambda Executor Provider
# ============================================================


class LambdaExecutorProvider(CodeExecProvider):
    """
    Execute code via AWS Lambda.

    Serverless execution with automatic scaling and isolation.
    Requires: boto3, AWS credentials, Lambda function deployed
    Configure with: AWS_LAMBDA_FUNCTION_NAME
    """

    def __init__(self) -> None:
        try:
            import boto3
        except ImportError as e:
            raise ValueError(
                "LambdaExecutorProvider requires 'boto3'. "
                "Install with: pip install boto3"
            ) from e

        self.lambda_client = boto3.client("lambda")
        self.function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME")

        if not self.function_name:
            raise ValueError(
                "LambdaExecutorProvider requires AWS_LAMBDA_FUNCTION_NAME environment variable"
            )

    def execute(self, language: str, source: str, timeout_s: int) -> dict[str, Any]:
        payload = {
            "language": language,
            "source": source,
            "timeout_s": timeout_s,
        }

        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        result = json.loads(response["Payload"].read())

        return {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", 0),
            "language": language,
        }


# ============================================================
# Sandbox API Provider
# ============================================================


class SandboxAPIProvider(CodeExecProvider):
    """
    Execute code via third-party sandbox API (e.g., Judge0, Piston).

    Uses external sandboxed execution service.
    Configure with: SANDBOX_API_URL, SANDBOX_API_KEY
    """

    def __init__(self) -> None:
        import requests

        self.api_url = os.getenv("SANDBOX_API_URL")
        if not self.api_url:
            raise ValueError(
                "SandboxAPIProvider requires SANDBOX_API_URL environment variable. "
                "Example: https://api.judge0.com/submissions"
            )

        self.api_key = os.getenv("SANDBOX_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["X-Auth-Token"] = self.api_key

    def execute(self, language: str, source: str, timeout_s: int) -> dict[str, Any]:
        if not self.api_url:
            raise RuntimeError("SANDBOX_API_URL environment variable not set")

        # Submit code execution request
        payload = {
            "language": language,
            "source_code": source,
            "cpu_time_limit": timeout_s,
        }

        response = self.session.post(self.api_url, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        return {
            "stdout": data.get("stdout", ""),
            "stderr": data.get("stderr", ""),
            "exit_code": data.get("exit_code", 0),
            "language": language,
        }


# ============================================================
# Provider Registry
# ============================================================


def register_code_exec_provider(name: str, provider_class: type[CodeExecProvider]) -> None:
    """
    Register a custom code execution provider.

    Args:
        name: Provider name (e.g., "docker", "lambda", "custom")
        provider_class: Provider class (subclass of CodeExecProvider)

    Example:
        register_code_exec_provider("lambda", LambdaExecutorProvider)
    """
    _CODE_EXEC_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered code exec provider: {name}")


def get_code_exec_provider(name: str) -> CodeExecProvider | ProviderRouter[CodeExecProvider]:
    """
    Get a code execution provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "lambda,docker,local")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (e.g., "local", "docker", "lambda", "sandbox") or comma-separated list

    Returns:
        CodeExecProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or instantiation fails

    Examples:
        # Single provider
        provider = get_code_exec_provider("docker")
        result = provider.execute("python", "print('hello')", 5)

        # Automatic fallback chain
        provider = get_code_exec_provider("lambda,docker,local")
        # Tries lambda first, falls back to docker, then local
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for code_exec: {provider_names}")
        return ProviderRouter(
            provider_getter=get_code_exec_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    # Register built-in providers on first access
    if not _CODE_EXEC_PROVIDERS:
        register_code_exec_provider("local", LocalExecutorProvider)
        register_code_exec_provider("docker", DockerExecutorProvider)
        register_code_exec_provider("lambda", LambdaExecutorProvider)
        register_code_exec_provider("aws-lambda", LambdaExecutorProvider)
        register_code_exec_provider("sandbox", SandboxAPIProvider)
        register_code_exec_provider("judge0", SandboxAPIProvider)

    if name not in _CODE_EXEC_PROVIDERS:
        available = ", ".join(sorted(_CODE_EXEC_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown code exec provider: {name}. "
            f"Available: {available}. "
            f"Register custom providers with register_code_exec_provider()."
        )

    try:
        return _CODE_EXEC_PROVIDERS[name]()
    except Exception as e:
        raise ValueError(f"Failed to initialize code exec provider '{name}': {e}") from e

"""
Bash execution provider adapters for stdlib bash (guarded) tool.

This module provides a unified interface for different bash execution backends
(local shell, SSH remote, Docker container, Kubernetes pod, etc.).

Users can add custom providers by:
1. Subclassing BashProvider
2. Implementing the execute() method
3. Registering with register_bash_provider()

Example custom provider:
    class SSHProvider(BashProvider):
        def execute(self, command: str, timeout_s: int, allowlist_paths: list[str] | None) -> dict:
            # Execute on remote host via SSH
            result = subprocess.run(
                ["ssh", "user@host", command],
                capture_output=True,
                timeout=timeout_s,
            )
            return {"stdout": result.stdout.decode(), ...}

    register_bash_provider("ssh", SSHProvider)
"""

from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available bash providers
_BASH_PROVIDERS: dict[str, type[BashProvider]] = {}


# ============================================================
# Base Bash Provider Interface
# ============================================================


class BashProvider(ABC):
    """
    Base class for bash execution providers.

    Subclass this to add support for different execution environments
    (SSH, Docker, Kubernetes, etc.).
    """

    @abstractmethod
    def execute(
        self,
        command: str,
        timeout_s: int,
        allowlist_paths: list[str] | None,
    ) -> dict[str, Any]:
        """
        Execute a bash command.

        Args:
            command: Bash command to execute (already validated)
            timeout_s: Timeout in seconds (already capped)
            allowlist_paths: Optional list of allowed paths

        Returns:
            Dictionary containing:
            - stdout (str): Standard output
            - stderr (str): Standard error
            - exit_code (int): Exit code (0 = success)
            - command (str): Command executed

        Raises:
            Exception: If execution fails (caught by caller)
        """
        pass


# ============================================================
# Local Bash Provider (Default)
# ============================================================


class LocalBashProvider(BashProvider):
    """
    Execute bash commands locally.

    WARNING: This executes untrusted commands locally! Use only in controlled environments.
    Consider using Docker or SSH providers for production.
    """

    def execute(
        self,
        command: str,
        timeout_s: int,
        allowlist_paths: list[str] | None,
    ) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                cwd=os.getcwd(),
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "command": command,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout_s}s",
                "exit_code": 124,
                "command": command,
            }


# ============================================================
# SSH Provider
# ============================================================


class SSHProvider(BashProvider):
    """
    Execute bash commands on remote host via SSH.

    Configure with: SSH_HOST, SSH_USER, SSH_PORT, SSH_KEY_PATH
    """

    def __init__(self) -> None:
        self.host = os.getenv("SSH_HOST")
        self.user = os.getenv("SSH_USER", "ubuntu")
        self.port = os.getenv("SSH_PORT", "22")
        self.key_path = os.getenv("SSH_KEY_PATH")

        if not self.host:
            raise ValueError(
                "SSHProvider requires SSH_HOST environment variable"
            )

    def execute(
        self,
        command: str,
        timeout_s: int,
        allowlist_paths: list[str] | None,
    ) -> dict[str, Any]:
        ssh_cmd = ["ssh"]

        if self.key_path:
            ssh_cmd += ["-i", self.key_path]

        ssh_cmd += [
            "-p", self.port,
            f"{self.user}@{self.host}",
            command,
        ]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "command": command,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"SSH command timed out after {timeout_s}s",
                "exit_code": 124,
                "command": command,
            }


# ============================================================
# Docker Provider
# ============================================================


class DockerProvider(BashProvider):
    """
    Execute bash commands in Docker container.

    Configure with: DOCKER_BASH_IMAGE (default: ubuntu:22.04)
    """

    def execute(
        self,
        command: str,
        timeout_s: int,
        allowlist_paths: list[str] | None,
    ) -> dict[str, Any]:
        image = os.getenv("DOCKER_BASH_IMAGE", "ubuntu:22.04")

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",  # No network access
            "--memory", "512m",
            "--cpus", "1",
            image,
            "bash", "-c", command,
        ]

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "command": command,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Docker command timed out after {timeout_s}s",
                "exit_code": 124,
                "command": command,
            }


# ============================================================
# Kubernetes Provider
# ============================================================


class KubernetesProvider(BashProvider):
    """
    Execute bash commands in Kubernetes pod.

    Configure with: K8S_NAMESPACE, K8S_POD_NAME (or K8S_DEPLOYMENT_NAME)
    """

    def __init__(self) -> None:
        self.namespace = os.getenv("K8S_NAMESPACE", "default")
        self.pod_name = os.getenv("K8S_POD_NAME")
        self.deployment_name = os.getenv("K8S_DEPLOYMENT_NAME")

        if not self.pod_name and not self.deployment_name:
            raise ValueError(
                "KubernetesProvider requires K8S_POD_NAME or K8S_DEPLOYMENT_NAME environment variable"
            )

    def _get_pod_name(self) -> str:
        """Get pod name (either directly or from deployment)."""
        if self.pod_name:
            return self.pod_name

        # Get pod from deployment
        result = subprocess.run(
            [
                "kubectl", "get", "pods",
                "-n", self.namespace,
                "-l", f"app={self.deployment_name}",
                "-o", "jsonpath={.items[0].metadata.name}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to get pod from deployment: {result.stderr}")

        pod_name = result.stdout.strip()
        assert isinstance(pod_name, str)
        return pod_name

    def execute(
        self,
        command: str,
        timeout_s: int,
        allowlist_paths: list[str] | None,
    ) -> dict[str, Any]:
        try:
            pod_name = self._get_pod_name()

            kubectl_cmd = [
                "kubectl", "exec",
                "-n", self.namespace,
                pod_name,
                "--",
                "bash", "-c", command,
            ]

            result = subprocess.run(
                kubectl_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "command": command,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Kubernetes command timed out after {timeout_s}s",
                "exit_code": 124,
                "command": command,
            }


# ============================================================
# Provider Registry
# ============================================================


def register_bash_provider(name: str, provider_class: type[BashProvider]) -> None:
    """
    Register a custom bash provider.

    Args:
        name: Provider name (e.g., "ssh", "docker", "custom")
        provider_class: Provider class (subclass of BashProvider)

    Example:
        register_bash_provider("ssh", SSHProvider)
    """
    _BASH_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered bash provider: {name}")


def get_bash_provider(name: str) -> BashProvider | ProviderRouter[BashProvider]:
    """
    Get a bash provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "docker,local")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (e.g., "local", "ssh", "docker", "kubernetes") or comma-separated list

    Returns:
        BashProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or instantiation fails

    Examples:
        # Single provider
        provider = get_bash_provider("docker")
        result = provider.execute("ls -la", 5, None)

        # Automatic fallback chain
        provider = get_bash_provider("docker,local")
        # Tries docker first, falls back to local if docker unavailable
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for bash: {provider_names}")
        return ProviderRouter(
            provider_getter=get_bash_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    # Register built-in providers on first access
    if not _BASH_PROVIDERS:
        register_bash_provider("local", LocalBashProvider)
        register_bash_provider("ssh", SSHProvider)
        register_bash_provider("remote", SSHProvider)
        register_bash_provider("docker", DockerProvider)
        register_bash_provider("kubernetes", KubernetesProvider)
        register_bash_provider("k8s", KubernetesProvider)

    if name not in _BASH_PROVIDERS:
        available = ", ".join(sorted(_BASH_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown bash provider: {name}. "
            f"Available: {available}. "
            f"Register custom providers with register_bash_provider()."
        )

    try:
        return _BASH_PROVIDERS[name]()
    except Exception as e:
        raise ValueError(f"Failed to initialize bash provider '{name}': {e}") from e

"""
File editing provider adapters for stdlib text_edit (guarded) tool.

This module provides a unified interface for different file storage backends
(local filesystem, S3, Git, SFTP, etc.).

Users can add custom providers by:
1. Subclassing TextEditProvider
2. Implementing the read(), write(), append(), delete() methods
3. Registering with register_text_edit_provider()

Example custom provider:
    class S3Provider(TextEditProvider):
        def read(self, path: str) -> dict:
            # Read from S3
            obj = s3_client.get_object(Bucket=bucket, Key=path)
            return {"path": path, "content": obj["Body"].read().decode()}

    register_text_edit_provider("s3", S3Provider)
"""

from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .provider_router import ProviderRouter

logger = logging.getLogger(__name__)

# Registry of available text edit providers
_TEXT_EDIT_PROVIDERS: dict[str, type[TextEditProvider]] = {}


# ============================================================
# Base Text Edit Provider Interface
# ============================================================


class TextEditProvider(ABC):
    """
    Base class for file editing providers.

    Subclass this to add support for different storage backends
    (S3, Git, SFTP, etc.).
    """

    @abstractmethod
    def read(self, path: str) -> dict[str, Any]:
        """
        Read file contents.

        Args:
            path: File path (already validated)

        Returns:
            Dictionary containing:
            - path (str): File path
            - content (str): File contents
            - exists (bool): Whether file exists

        Raises:
            Exception: If read fails (caught by caller)
        """
        pass

    @abstractmethod
    def write(self, path: str, content: str) -> dict[str, Any]:
        """
        Write (overwrite) file contents.

        Args:
            path: File path (already validated)
            content: Content to write

        Returns:
            Dictionary containing:
            - path (str): File path
            - written (bool): Whether write succeeded
            - bytes (int): Bytes written

        Raises:
            Exception: If write fails (caught by caller)
        """
        pass

    @abstractmethod
    def append(self, path: str, content: str) -> dict[str, Any]:
        """
        Append to file contents.

        Args:
            path: File path (already validated)
            content: Content to append

        Returns:
            Dictionary containing:
            - path (str): File path
            - appended (bool): Whether append succeeded
            - bytes (int): Bytes appended

        Raises:
            Exception: If append fails (caught by caller)
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> dict[str, Any]:
        """
        Delete a file.

        Args:
            path: File path (already validated)

        Returns:
            Dictionary containing:
            - path (str): File path
            - deleted (bool): Whether delete succeeded

        Raises:
            Exception: If delete fails (caught by caller)
        """
        pass


# ============================================================
# Local Filesystem Provider (Default)
# ============================================================


class LocalFilesystemProvider(TextEditProvider):
    """
    Read/write files on local filesystem.

    Standard file operations using Python's pathlib.
    """

    def read(self, path: str) -> dict[str, Any]:
        file_path = Path(path)

        if not file_path.exists():
            return {
                "path": path,
                "content": "",
                "exists": False,
            }

        content = file_path.read_text(encoding="utf-8")

        return {
            "path": path,
            "content": content,
            "exists": True,
        }

    def write(self, path: str, content: str) -> dict[str, Any]:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding="utf-8")
        bytes_written = file_path.stat().st_size

        logger.debug(f"LocalFilesystem: wrote {bytes_written} bytes to {path}")
        return {
            "path": path,
            "written": True,
            "bytes": bytes_written,
        }

    def append(self, path: str, content: str) -> dict[str, Any]:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("a", encoding="utf-8") as f:
            f.write(content)

        bytes_appended = len(content.encode("utf-8"))

        logger.debug(f"LocalFilesystem: appended {bytes_appended} bytes to {path}")
        return {
            "path": path,
            "appended": True,
            "bytes": bytes_appended,
        }

    def delete(self, path: str) -> dict[str, Any]:
        file_path = Path(path)

        if file_path.exists():
            file_path.unlink()
            return {"path": path, "deleted": True}

        return {"path": path, "deleted": False}


# ============================================================
# S3 Provider
# ============================================================


class S3Provider(TextEditProvider):
    """
    Read/write files to AWS S3.

    Requires: pip install boto3
    Configure with: S3_BUCKET, AWS credentials (via environment or ~/.aws/credentials)
    """

    def __init__(self) -> None:
        try:
            import boto3
        except ImportError as e:
            raise ValueError(
                "S3Provider requires 'boto3'. "
                "Install with: pip install boto3"
            ) from e

        self.s3_client = boto3.client("s3")
        self.bucket = os.getenv("S3_BUCKET")

        if not self.bucket:
            raise ValueError(
                "S3Provider requires S3_BUCKET environment variable"
            )

    def read(self, path: str) -> dict[str, Any]:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=path)
            content = response["Body"].read().decode("utf-8")

            return {
                "path": path,
                "content": content,
                "exists": True,
            }

        except self.s3_client.exceptions.NoSuchKey:
            return {
                "path": path,
                "content": "",
                "exists": False,
            }

    def write(self, path: str, content: str) -> dict[str, Any]:
        content_bytes = content.encode("utf-8")

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=content_bytes,
        )

        logger.debug(f"S3: wrote {len(content_bytes)} bytes to s3://{self.bucket}/{path}")
        return {
            "path": path,
            "written": True,
            "bytes": len(content_bytes),
        }

    def append(self, path: str, content: str) -> dict[str, Any]:
        # Read existing content, append, and write back
        existing = self.read(path)
        new_content = existing.get("content", "") + content

        return self.write(path, new_content)

    def delete(self, path: str) -> dict[str, Any]:
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=path)
            return {"path": path, "deleted": True}
        except Exception:
            return {"path": path, "deleted": False}


# ============================================================
# Git Provider
# ============================================================


class GitProvider(TextEditProvider):
    """
    Read/write files with automatic git commits.

    Wraps local filesystem operations with git add + commit.
    Configure with: GIT_AUTO_COMMIT (default: true), GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL
    """

    def __init__(self) -> None:
        self.local_provider = LocalFilesystemProvider()
        self.auto_commit = os.getenv("GIT_AUTO_COMMIT", "true").lower() == "true"
        self.author_name = os.getenv("GIT_AUTHOR_NAME", "ToolWeaver")
        self.author_email = os.getenv("GIT_AUTHOR_EMAIL", "toolweaver@example.com")

    def _git_commit(self, path: str, operation: str) -> None:
        """Auto-commit changes if enabled."""
        if not self.auto_commit:
            return

        try:
            # Stage file
            subprocess.run(
                ["git", "add", path],
                check=True,
                capture_output=True,
            )

            # Commit
            subprocess.run(
                [
                    "git", "commit",
                    "-m", f"[ToolWeaver] {operation}: {path}",
                    "--author", f"{self.author_name} <{self.author_email}>",
                ],
                check=True,
                capture_output=True,
            )

            logger.debug(f"Git: committed {operation} for {path}")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Git commit failed: {e}")

    def read(self, path: str) -> dict[str, Any]:
        result: dict[str, Any] = self.local_provider.read(path)
        return result

    def write(self, path: str, content: str) -> dict[str, Any]:
        result: dict[str, Any] = self.local_provider.write(path, content)
        self._git_commit(path, "write")
        return result

    def append(self, path: str, content: str) -> dict[str, Any]:
        result: dict[str, Any] = self.local_provider.append(path, content)
        self._git_commit(path, "append")
        return result

    def delete(self, path: str) -> dict[str, Any]:
        result: dict[str, Any] = self.local_provider.delete(path)

        if result["deleted"]:
            # Use git rm instead of manual commit
            try:
                subprocess.run(
                    ["git", "rm", path],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        "git", "commit",
                        "-m", f"[ToolWeaver] delete: {path}",
                        "--author", f"{self.author_name} <{self.author_email}>",
                    ],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                logger.warning(f"Git rm failed: {e}")

        return result


# ============================================================
# SFTP Provider
# ============================================================


class SFTPProvider(TextEditProvider):
    """
    Read/write files via SFTP.

    Requires: pip install paramiko
    Configure with: SFTP_HOST, SFTP_USER, SFTP_PASSWORD or SFTP_KEY_PATH
    """

    def __init__(self) -> None:
        try:
            import paramiko
        except ImportError as e:
            raise ValueError(
                "SFTPProvider requires 'paramiko'. "
                "Install with: pip install paramiko"
            ) from e

        self.host = os.getenv("SFTP_HOST")
        self.user = os.getenv("SFTP_USER")
        self.password = os.getenv("SFTP_PASSWORD")
        self.key_path = os.getenv("SFTP_KEY_PATH")
        self.port = int(os.getenv("SFTP_PORT", "22"))

        if not self.host or not self.user:
            raise ValueError(
                "SFTPProvider requires SFTP_HOST and SFTP_USER environment variables"
            )

        # Create SSH client
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect
        if self.key_path:
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                key_filename=self.key_path,
            )
        elif self.password:
            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
            )
        else:
            raise ValueError("SFTPProvider requires SFTP_PASSWORD or SFTP_KEY_PATH")

        self.sftp_client = self.ssh_client.open_sftp()

    def read(self, path: str) -> dict[str, Any]:
        try:
            with self.sftp_client.open(path, "r") as f:
                content = f.read().decode("utf-8")

            return {
                "path": path,
                "content": content,
                "exists": True,
            }

        except FileNotFoundError:
            return {
                "path": path,
                "content": "",
                "exists": False,
            }

    def write(self, path: str, content: str) -> dict[str, Any]:
        content_bytes = content.encode("utf-8")

        with self.sftp_client.open(path, "w") as f:
            f.write(content_bytes)

        logger.debug(f"SFTP: wrote {len(content_bytes)} bytes to {path}")
        return {
            "path": path,
            "written": True,
            "bytes": len(content_bytes),
        }

    def append(self, path: str, content: str) -> dict[str, Any]:
        # Read existing content, append, and write back
        existing = self.read(path)
        new_content = existing.get("content", "") + content

        return self.write(path, new_content)

    def delete(self, path: str) -> dict[str, Any]:
        try:
            self.sftp_client.remove(path)
            return {"path": path, "deleted": True}
        except Exception:
            return {"path": path, "deleted": False}


# ============================================================
# Provider Registry
# ============================================================


def register_text_edit_provider(name: str, provider_class: type[TextEditProvider]) -> None:
    """
    Register a custom text edit provider.

    Args:
        name: Provider name (e.g., "s3", "git", "custom")
        provider_class: Provider class (subclass of TextEditProvider)

    Example:
        register_text_edit_provider("s3", S3Provider)
    """
    _TEXT_EDIT_PROVIDERS[name.lower()] = provider_class
    logger.info(f"Registered text edit provider: {name}")


def get_text_edit_provider(name: str) -> TextEditProvider | ProviderRouter[TextEditProvider]:
    """
    Get a text edit provider instance by name.

    Supports automatic fallback chains: Pass comma-separated names (e.g., "s3,local")
    to create a ProviderRouter with FALLBACK strategy.

    Args:
        name: Provider name (e.g., "local", "s3", "git", "sftp") or comma-separated list

    Returns:
        TextEditProvider instance or ProviderRouter

    Raises:
        ValueError: If provider not found or instantiation fails

    Examples:
        # Single provider
        provider = get_text_edit_provider("git")
        provider.write("/tmp/test.txt", "hello world")

        # Automatic fallback chain
        provider = get_text_edit_provider("s3,local")
        # Tries S3 first, falls back to local filesystem
    """
    from .provider_router import ProviderRouter, RouterStrategy

    # Check for comma-separated fallback chain
    if "," in name:
        provider_names = [p.strip() for p in name.split(",")]
        logger.info(f"Creating fallback chain for text_edit: {provider_names}")
        return ProviderRouter(
            provider_getter=get_text_edit_provider,
            providers=provider_names,
            strategy=RouterStrategy.FALLBACK,
            circuit_breaker_enabled=True,
        )

    name = name.lower()

    # Register built-in providers on first access
    if not _TEXT_EDIT_PROVIDERS:
        register_text_edit_provider("local", LocalFilesystemProvider)
        register_text_edit_provider("filesystem", LocalFilesystemProvider)
        register_text_edit_provider("s3", S3Provider)
        register_text_edit_provider("git", GitProvider)
        register_text_edit_provider("sftp", SFTPProvider)

    if name not in _TEXT_EDIT_PROVIDERS:
        available = ", ".join(sorted(_TEXT_EDIT_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown text edit provider: {name}. "
            f"Available: {available}. "
            f"Register custom providers with register_text_edit_provider()."
        )

    try:
        return _TEXT_EDIT_PROVIDERS[name]()
    except Exception as e:
        raise ValueError(f"Failed to initialize text edit provider '{name}': {e}") from e

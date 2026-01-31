"""
Ollama Embedding Model Wrapper

Provides access to local embedding models via Ollama (e.g., nomic-embed-text, mxbai-embed-large).
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

class OllamaEmbeddingModel:
    """Wrapper for Ollama-hosted embedding models."""

    def __init__(self, model_name: str = "nomic-embed-text"):
        """
        Initialize Ollama embedding model.

        Args:
            model_name: The model tag in Ollama (e.g. 'nomic-embed-text').
        """
        self.model_name = model_name
        # Use valid OLLAMA_HOST or default
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.base_url = host.rstrip("/")

    def encode(
        self, text: str | list[str], convert_to_tensor: bool = False
    ) -> list[float] | list[list[float]]:
        """
        Generate embedding(s) for text using Ollama.

        Args:
            text: Single text string or list of strings
            convert_to_tensor: Ignored

        Returns:
            Embedding vector or list of vectors
        """
        is_list = isinstance(text, list)
        texts: list[str] = text if is_list else [text]  # type: ignore

        embeddings = []
        url = f"{self.base_url}/api/embeddings"

        for t in texts:
            try:
                response = requests.post(
                    url,
                    json={"model": self.model_name, "prompt": t},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                if "embedding" not in data:
                    raise ValueError(f"No embedding in response: {data}")
                embeddings.append(data["embedding"])
            except Exception as e:
                logger.error(f"Ollama Embedding failed for text '{t[:20]}...': {e}")
                # We can't partial fail easily in this interface, so we raise
                raise e

        return embeddings[0] if not is_list else embeddings

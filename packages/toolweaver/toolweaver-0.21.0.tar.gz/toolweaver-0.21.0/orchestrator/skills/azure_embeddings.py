"""
Azure OpenAI Embedding Model Wrapper

Provides access to Azure-hosted embedding models (e.g., text-embedding-ada-002, 3-small/large).
"""

import logging
import os

logger = logging.getLogger(__name__)

class AzureEmbeddingModel:
    """Wrapper for Azure OpenAI embedding models."""

    def __init__(self, model_name: str = "text-embedding-ada-002"):
        """
        Initialize Azure embedding model.

        Args:
            model_name: The deployment name (not just model name) in Azure.
        """
        self.model_name = model_name
        self.api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_base: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        if not self.api_key or not self.api_base:
            raise ValueError(
                "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set."
            )

        # Ensure they are strings for type checkers
        self.api_key = str(self.api_key)
        self.api_base = str(self.api_base)

    def encode(
        self, text: str | list[str], convert_to_tensor: bool = False
    ) -> list[float] | list[list[float]]:
        """
        Generate embedding(s) for text using Azure OpenAI.

        Args:
            text: Single text string or list of strings
            convert_to_tensor: Ignored

        Returns:
            Embedding vector or list of vectors
        """
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("openai package not installed.") from None

        is_list = isinstance(text, list)
        texts: list[str] = text if is_list else [text]  # type: ignore

        if not self.api_key or not self.api_base:
             raise ValueError("API Key and Base must be set")

        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base
        )

        try:
            # Azure uses 'model' param relative to deployment
            response = client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            return embeddings[0] if not is_list else embeddings
        except Exception as e:
            logger.error(f"Azure Embedding failed: {e}")
            raise e

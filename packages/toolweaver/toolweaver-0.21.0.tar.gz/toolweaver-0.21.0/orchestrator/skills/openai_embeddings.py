"""
OpenAI Embedding Model Wrapper

Provides unified interface to OpenAI's text-embedding models via their API.
"""

import os


class OpenAIEmbeddingModel:
    """
    Wrapper for OpenAI embedding models (text-embedding-3-small, text-embedding-3-large).

    Supports:
    - text-embedding-3-small (1536 dimensions, $0.02/1M tokens)
    - text-embedding-3-large (3072 dimensions, $0.13/1M tokens)
    """

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding model.

        Args:
            model_name: Model name ('text-embedding-3-small' or 'text-embedding-3-large')
        """
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_EMBEDDING_API_KEY")
        self.org_id = os.getenv("OPENAI_EMBEDDING_ORG_ID")

        if not self.api_key:
            raise ValueError(
                "OPENAI_EMBEDDING_API_KEY not set. Please set it in your .env file or environment."
            )

        # Model dimensions
        self.dimension_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

        if model_name not in self.dimension_map:
            raise ValueError(
                f"Unknown OpenAI embedding model: {model_name}. "
                f"Supported models: {list(self.dimension_map.keys())}"
            )

        self.dimension = self.dimension_map[model_name]

    def encode(
        self, text: str | list[str], convert_to_tensor: bool = False
    ) -> list[float] | list[list[float]]:
        """
        Generate embedding(s) for text using OpenAI API.

        Args:
            text: Single text string or list of strings
            convert_to_tensor: Ignored (for compatibility with SentenceTransformer interface)

        Returns:
            Embedding vector or list of vectors as floats
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            ) from None

        # Normalize input
        from typing import Any

        is_list = isinstance(text, list)
        texts: list[str]
        if is_list:
            # Flatten if needed and ensure all str - mypy struggles with union in list comprehension
            text_list: Any = text
            texts = [str(item) for item in text_list]
        else:
            texts = [text]  # type: ignore[list-item]

        # Call OpenAI API
        client = OpenAI(api_key=self.api_key, organization=self.org_id if self.org_id else None)

        response = client.embeddings.create(model=self.model_name, input=texts)

        # Extract embeddings
        embeddings = [item.embedding for item in response.data]

        # Return single embedding or list
        return embeddings[0] if not is_list else embeddings

    def __repr__(self) -> str:
        return f"OpenAIEmbeddingModel(model='{self.model_name}', dim={self.dimension})"

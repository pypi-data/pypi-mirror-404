"""
Instrument Loader - Abstract Base Class

Defines the interface for loading agent instruments (tools/skills).
Instruments are Agent Zero style markdown files with embedded prompts.

Phase 4: File-based markdown instruments
Phase 5: Database-backed instruments
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class InstrumentError(Exception):
    """Raised when instrument operations fail."""

    pass


class InstrumentLoader(ABC):
    """
    Abstract base class for instrument loading strategies.

    Instruments are Agent Zero style markdown files containing:
    - Tool descriptions
    - Usage prompts
    - Example invocations
    - Parameter specifications

    Example:
        loader = get_instrument_loader("markdown")
        instrument = loader.load_instrument("./instruments/search.md")
        print(instrument["prompt"])
    """

    @abstractmethod
    def load_instrument(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """
        Load an instrument from a path.

        Args:
            path: Path to instrument (file path, URL, database ID)
            **kwargs: Implementation-specific options

        Returns:
            Instrument dictionary with keys like:
            - name: str
            - description: str
            - prompt: str
            - examples: List[str]
            - parameters: Dict[str, Any]

        Raises:
            InstrumentError: If loading fails
        """
        pass

    @abstractmethod
    def parse_markdown(self, content: str, **kwargs: Any) -> dict[str, Any]:
        """
        Parse markdown content into instrument structure.

        Args:
            content: Markdown text
            **kwargs: Parsing options

        Returns:
            Parsed instrument dictionary

        Raises:
            InstrumentError: If parsing fails
        """
        pass

    @abstractmethod
    def list_instruments(self, directory: str, **kwargs: Any) -> list[str]:
        """
        List available instruments in a directory/collection.

        Args:
            directory: Directory path or collection identifier
            **kwargs: Implementation-specific options

        Returns:
            List of instrument paths/identifiers
        """
        pass

    @abstractmethod
    def validate_instrument(self, instrument: dict[str, Any], **kwargs: Any) -> bool:
        """
        Validate instrument structure.

        Args:
            instrument: Instrument data to validate
            **kwargs: Validation options

        Returns:
            True if valid

        Raises:
            InstrumentError: If validation fails
        """
        pass


def get_instrument_loader(loader_type: str = "markdown", **kwargs: Any) -> InstrumentLoader:
    """
    Factory function to get instrument loader instance.

    Args:
        loader_type: Type of loader ("markdown", "database")
        **kwargs: Loader-specific initialization parameters

    Returns:
        InstrumentLoader instance

    Raises:
        ValueError: If loader_type is unknown
        InstrumentError: If initialization fails

    Example:
        # Markdown loader (default)
        loader = get_instrument_loader("markdown")
        instrument = loader.load_instrument("./instruments/search.md")

        # Database loader (Phase 5)
        loader = get_instrument_loader("database", db_url="postgresql://...")
    """
    from .markdown import MarkdownInstrumentLoader

    loaders = {
        "markdown": MarkdownInstrumentLoader,
    }

    # Phase 5: Add database loader
    # try:
    #     from .database import DatabaseInstrumentLoader
    #     loaders["database"] = DatabaseInstrumentLoader
    # except ImportError:
    #     pass

    loader_class = loaders.get(loader_type)
    if not loader_class:
        available = ", ".join(loaders.keys())
        raise ValueError(f"Unknown loader type: {loader_type}. Available loaders: {available}")

    try:
        return loader_class(**kwargs)
    except Exception as e:
        raise InstrumentError(f"Failed to initialize {loader_type} loader: {e}") from e

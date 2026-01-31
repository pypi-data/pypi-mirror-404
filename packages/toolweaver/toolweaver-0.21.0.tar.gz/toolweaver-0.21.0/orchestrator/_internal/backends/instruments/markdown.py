"""
Markdown Instrument Loader

Loads Agent Zero style markdown instruments from files.
Parses structured markdown into instrument dictionaries.
"""

import logging
import re
from pathlib import Path
from typing import Any

from .base import InstrumentError, InstrumentLoader

logger = logging.getLogger(__name__)


class MarkdownInstrumentLoader(InstrumentLoader):
    """
    Load instruments from markdown files.

    Expected format (Agent Zero style):
        # Instrument Name

        Brief description of the instrument.

        ## Usage
        When to use this instrument...

        ## Examples
        - Example 1
        - Example 2

        ## Prompt
        System prompt for using this instrument...

    Example:
        loader = MarkdownInstrumentLoader()
        instrument = loader.load_instrument("./instruments/search.md")
        print(instrument["prompt"])
    """

    def __init__(self) -> None:
        """Initialize markdown instrument loader."""
        logger.info("Initialized MarkdownInstrumentLoader")

    def load_instrument(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Load instrument from markdown file."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise InstrumentError(f"Instrument not found: {path}")

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            instrument = self.parse_markdown(content)
            instrument["path"] = str(file_path)
            instrument["name"] = instrument.get("name") or file_path.stem

            logger.debug(f"Loaded instrument: {instrument['name']}")
            return instrument

        except OSError as e:
            raise InstrumentError(f"Failed to load instrument {path}: {e}") from None

    def parse_markdown(self, content: str, **kwargs: Any) -> dict[str, Any]:
        """Parse markdown content into instrument structure."""
        instrument = {
            "name": "",
            "description": "",
            "usage": "",
            "examples": [],
            "prompt": "",
        }

        # Extract title (# Title)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            instrument["name"] = title_match.group(1).strip()

        # Extract sections
        sections = re.split(r"^##\s+(.+)$", content, flags=re.MULTILINE)

        # First section is description (before any ##)
        if sections:
            desc = sections[0].replace(title_match.group(0) if title_match else "", "")
            instrument["description"] = desc.strip()

        # Parse remaining sections
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_title = sections[i].strip().lower()
                section_content = sections[i + 1].strip()

                if "usage" in section_title:
                    instrument["usage"] = section_content
                elif "example" in section_title:
                    # Extract bullet points
                    examples = re.findall(r"^[-*]\s+(.+)$", section_content, re.MULTILINE)
                    instrument["examples"] = examples
                elif "prompt" in section_title:
                    instrument["prompt"] = section_content

        return instrument

    def list_instruments(self, directory: str, **kwargs: Any) -> list[str]:
        """List all markdown files in directory."""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []

            instruments = []
            for file_path in dir_path.glob("*.md"):
                instruments.append(str(file_path))

            return sorted(instruments)

        except Exception as e:
            raise InstrumentError(f"Failed to list instruments in {directory}: {e}") from None

    def validate_instrument(self, instrument: dict[str, Any], **kwargs: Any) -> bool:
        """Validate instrument has required fields."""
        if not isinstance(instrument, dict):
            raise InstrumentError("Instrument must be a dictionary")

        # Name is required
        if not instrument.get("name"):
            raise InstrumentError("Instrument must have a 'name'")

        # Warn if missing recommended fields
        if not instrument.get("prompt"):
            logger.warning(f"Instrument '{instrument['name']}' missing prompt")

        return True

    def __repr__(self) -> str:
        return "MarkdownInstrumentLoader()"

"""
Instrument Loader Package (DEPRECATED - use _internal.backends.instruments).

Provides pluggable loaders for agent instruments (Agent Zero style).

Re-exports from new location for backwards compatibility.
"""

from orchestrator._internal.backends.instruments.base import (
    InstrumentError,
    InstrumentLoader,
    get_instrument_loader,
)
from orchestrator._internal.backends.instruments.markdown import MarkdownInstrumentLoader

__all__ = [
    "InstrumentLoader",
    "InstrumentError",
    "get_instrument_loader",
    "MarkdownInstrumentLoader",
]

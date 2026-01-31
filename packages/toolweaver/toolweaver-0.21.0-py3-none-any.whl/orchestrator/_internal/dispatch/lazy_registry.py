"""Lazy registration utilities for on-demand tool loading.

This module provides utilities to register tools/adapters only when explicitly needed,
reducing import-time side effects and log noise.
"""

from collections.abc import Callable


def register_example_functions() -> None:
    """Register example structured functions for testing and demos.

    Call this explicitly in samples/tests that need the example functions.
    These functions are: compute_tax, merge_items, apply_discount,
    filter_items_by_category, compute_item_statistics.
    """
    from . import functions as _  # noqa: F401
    # The import itself performs the registration via decorators


def register_weather_adapter(api_key: str) -> None:
    """Register MCP HTTP adapter for WeatherAPI.com on-demand.

    Args:
        api_key: WeatherAPI.com API key for authentication

    Example:
        >>> from orchestrator import register_weather_adapter
        >>> register_weather_adapter(os.getenv("WEATHER_API_KEY"))
    """
    from ...tools.mcp_adapter import register_mcp_http_adapter
    from ..infra.mcp_auth import MCPAuthConfig

    auth = MCPAuthConfig(
        type="api_key",
        token_env="WEATHER_API_KEY",
        header_name="X-API-Key",
    )

    register_mcp_http_adapter(
        name="weather_api",
        base_url="https://api.weatherapi.com/v1",
        auth=auth,
    )


# Registry of lazy loaders for discoverability
LAZY_LOADERS: dict[str, Callable[..., None]] = {
    "example_functions": register_example_functions,
    "weather_adapter": register_weather_adapter,
}

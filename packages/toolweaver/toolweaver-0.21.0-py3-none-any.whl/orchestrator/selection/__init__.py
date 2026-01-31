"""Selection strategies and routing facade.

Public exports: route_request, choose_model, set_available_models
"""

from .routing import choose_model, route_request, set_available_models

__all__ = [
    "route_request",
    "choose_model",
    "set_available_models",
]

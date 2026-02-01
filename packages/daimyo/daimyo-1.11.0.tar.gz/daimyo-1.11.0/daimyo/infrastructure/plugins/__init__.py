"""Plugin infrastructure for extensibility."""

from .discovery import PluginDiscoveryService
from .matcher import WildcardMatcher
from .registry import PluginRegistry

__all__ = [
    "PluginDiscoveryService",
    "PluginRegistry",
    "WildcardMatcher",
]

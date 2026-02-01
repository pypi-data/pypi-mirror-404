"""
Daimyo - Rules Server for Agents

A Python server providing rules to agents through REST and MCP interfaces.
Supports scope-based rules with inheritance, categories for filtering,
and server federation for distributed rule management.
"""

from daimyo.application.validation import ValidationError
from daimyo.domain import (
    DaimyoError,
    InvalidScopeError,
    ScopeNotFoundError,
)

__version__ = "1.11.0"

__all__ = [
    "__version__",
    "DaimyoError",
    "ScopeNotFoundError",
    "InvalidScopeError",
    "ValidationError",
]

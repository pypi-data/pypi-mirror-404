"""Protocol definitions for domain interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Protocol

from .models import MergedScope, Scope


class ScopeRepository(Protocol):
    """Abstract interface for scope storage and retrieval."""

    def get_scope(self, name: str) -> Scope | None:
        """Retrieve a scope by name.

        :param name: The scope name
        :type name: str
        :returns: The scope if found, None otherwise
        :rtype: Optional[Scope]
        """

    def list_scopes(self) -> list[str]:
        """List all available scope names.

        :returns: List of scope names
        :rtype: list[str]
        """


class RemoteScopeClient(Protocol):
    """Abstract interface for retrieving scopes from remote servers."""

    def fetch_scope(self, url: str, scope_name: str) -> Scope | None:
        """Fetch a scope from a remote server.

        :param url: The base URL of the remote server
        :type url: str
        :param scope_name: The name of the scope to fetch
        :type scope_name: str
        :returns: The scope if found, None otherwise
        :rtype: Optional[Scope]
        :raises RemoteServerError: If the remote server is unreachable or returns an error
        """

    def list_scopes(self, url: str) -> list[str] | None:
        """List available scopes from a remote server.

        :param url: The base URL of the remote server
        :type url: str
        :returns: List of scope names if successful, None otherwise
        :rtype: Optional[list[str]]
        :raises RemoteServerError: If the remote server is unreachable or returns an error
        """


class FormatterProtocol(Protocol):
    """Abstract interface for formatting merged scopes."""

    def format(self, scope: MergedScope) -> str | dict:
        """Format a merged scope for output.

        :param scope: The merged scope to format
        :type scope: MergedScope
        :returns: Formatted output as string or dict
        :rtype: str | dict
        """


class BasePlugin(ABC):
    """Abstract base class for all daimyo plugins.

    Each plugin type should inherit from this and implement
    its specific functionality through dedicated methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier.

        :returns: Plugin name in dot-notation format (e.g., 'git.context')
        :rtype: str
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of plugin functionality.

        :returns: Plugin description
        :rtype: str
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if plugin can execute in current environment.

        :returns: True if plugin can provide functionality
        :rtype: bool
        """


class ContextProviderPlugin(BasePlugin):
    """Plugin that provides Jinja2 template context variables."""

    @abstractmethod
    def get_context(self, scope: MergedScope) -> dict[str, Any]:
        """Generate context variables for template rendering.

        :param scope: The merged scope being rendered
        :type scope: MergedScope
        :returns: Dictionary of context variables
        :rtype: dict[str, Any]
        """


class FilterProviderPlugin(BasePlugin):
    """Plugin that provides Jinja2 filters and tests."""

    @abstractmethod
    def get_filters(self) -> dict[str, Callable]:
        """Provide custom Jinja2 filters.

        :returns: Dictionary mapping filter names to filter functions
        :rtype: dict[str, Callable]
        """

    @abstractmethod
    def get_tests(self) -> dict[str, Callable]:
        """Provide custom Jinja2 tests.

        :returns: Dictionary mapping test names to test functions
        :rtype: dict[str, Callable]
        """


Plugin = BasePlugin

__all__ = [
    "ScopeRepository",
    "RemoteScopeClient",
    "FormatterProtocol",
    "BasePlugin",
    "ContextProviderPlugin",
    "FilterProviderPlugin",
    "Plugin",
]

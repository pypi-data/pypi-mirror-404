"""Domain-specific exceptions."""

from __future__ import annotations


class DaimyoError(Exception):
    """Base exception for all Daimyo errors."""


class ScopeNotFoundError(DaimyoError):
    """Raised when a requested scope does not exist."""

    def __init__(self, scope_name: str, available_scopes: list[str] | None = None):
        self.scope_name = scope_name
        self.available_scopes = available_scopes

        msg = f"Scope '{scope_name}' not found"
        if available_scopes:
            msg += f". Available scopes: {', '.join(available_scopes[:5])}"
            if len(available_scopes) > 5:
                msg += f" (and {len(available_scopes) - 5} more)"

        super().__init__(msg)


class InvalidScopeError(DaimyoError):
    """Raised when scope data is malformed or invalid."""


class CircularDependencyError(DaimyoError):
    """Raised when a circular parent reference is detected."""


class InheritanceDepthExceededError(CircularDependencyError):
    """Raised when maximum inheritance depth is exceeded."""


class RemoteServerError(DaimyoError):
    """Raised when communication with a remote server fails."""

    def __init__(self, message: str, url: str | None = None, status_code: int | None = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class RemoteScopeUnavailableError(RemoteServerError):
    """Raised when a remote scope is temporarily unavailable."""


class ScopeMergingError(DaimyoError):
    """Raised when merging scopes fails."""


class FormatterError(DaimyoError):
    """Raised when formatting a scope fails."""


class InvalidCategoryError(DaimyoError):
    """Raised when a category specification is invalid."""


class YAMLParseError(DaimyoError):
    """Raised when YAML parsing fails."""


class TemplateRenderingError(DaimyoError):
    """Raised when template rendering fails (e.g., undefined variable).

    This is a client error (4xx) - the template syntax is invalid or
    references undefined variables.
    """

    def __init__(self, template_text: str, variable_name: str, context_info: str = ""):
        self.template_text = template_text
        self.variable_name = variable_name
        self.context_info = context_info

        msg = f"Template variable '{variable_name}' is undefined"
        if context_info:
            msg += f" in {context_info}"
        msg += f"\n\nTemplate: {template_text[:100]}"
        if len(template_text) > 100:
            msg += "..."
        msg += "\n\nTip: Use Jinja2 'default' filter for optional variables: "
        msg += f"{{{{ {variable_name} | default('fallback') }}}}"

        super().__init__(msg)


class PluginError(DaimyoError):
    """Base exception for plugin-related errors."""


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found."""

    def __init__(self, plugin_name: str, available_plugins: list[str] | None = None):
        self.plugin_name = plugin_name
        self.available_plugins = available_plugins

        msg = f"Plugin '{plugin_name}' not found"
        if available_plugins:
            msg += f". Available plugins: {', '.join(available_plugins[:5])}"
            if len(available_plugins) > 5:
                msg += f" (and {len(available_plugins) - 5} more)"

        super().__init__(msg)


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""

    def __init__(self, plugin_name: str, message: str, original_error: Exception | None = None):
        self.plugin_name = plugin_name
        self.original_error = original_error

        msg = f"Plugin '{plugin_name}' execution failed: {message}"
        super().__init__(msg)


class PluginConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""


__all__ = [
    "DaimyoError",
    "ScopeNotFoundError",
    "InvalidScopeError",
    "CircularDependencyError",
    "InheritanceDepthExceededError",
    "RemoteServerError",
    "RemoteScopeUnavailableError",
    "ScopeMergingError",
    "FormatterError",
    "InvalidCategoryError",
    "YAMLParseError",
    "TemplateRenderingError",
    "PluginError",
    "PluginNotFoundError",
    "PluginExecutionError",
    "PluginConfigurationError",
]

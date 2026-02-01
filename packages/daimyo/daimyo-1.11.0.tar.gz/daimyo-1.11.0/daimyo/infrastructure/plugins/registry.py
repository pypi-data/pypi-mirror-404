"""Central registry for managing discovered plugins."""

from collections.abc import Callable
from typing import Any

from daimyo.domain import (
    BasePlugin,
    ContextProviderPlugin,
    FilterProviderPlugin,
    MergedScope,
    PluginExecutionError,
)
from daimyo.infrastructure.logging import get_logger
from daimyo.infrastructure.plugins.matcher import WildcardMatcher

logger = get_logger(__name__)


class PluginRegistry:
    """Central registry for plugins."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._plugins: dict[str, BasePlugin] = {}
        logger.debug("Initialized PluginRegistry")

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin.

        :param plugin: Plugin instance to register
        :type plugin: BasePlugin
        """
        if plugin.name in self._plugins:
            logger.warning(f"Plugin '{plugin.name}' already registered, overwriting")

        self._plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get plugin by name.

        :param name: Plugin name
        :type name: str
        :returns: Plugin instance or None if not found
        :rtype: BasePlugin | None
        """
        return self._plugins.get(name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names.

        :returns: List of plugin names
        :rtype: list[str]
        """
        return sorted(self._plugins.keys())

    def get_enabled_plugins(self, enabled_patterns: list[str]) -> list[BasePlugin]:
        """Get plugins matching enabled patterns.

        :param enabled_patterns: List of wildcard patterns
        :type enabled_patterns: list[str]
        :returns: List of enabled plugins
        :rtype: list[BasePlugin]
        """
        if not enabled_patterns:
            logger.debug("No enabled patterns, returning empty list")
            return []

        matcher = WildcardMatcher(enabled_patterns)
        enabled_names = matcher.filter_plugins(list(self._plugins.keys()))

        enabled_plugins = [self._plugins[name] for name in enabled_names]
        logger.info(f"Enabled {len(enabled_plugins)} plugins: {enabled_names}")

        return enabled_plugins

    def get_context_providers(self, enabled_patterns: list[str]) -> list[ContextProviderPlugin]:
        """Get enabled plugins that implement ContextProviderPlugin.

        :param enabled_patterns: List of enabled plugin patterns
        :type enabled_patterns: list[str]
        :returns: List of enabled context provider plugins
        :rtype: list[ContextProviderPlugin]
        """
        enabled = self.get_enabled_plugins(enabled_patterns)

        providers = [p for p in enabled if isinstance(p, ContextProviderPlugin)]

        logger.debug(f"Found {len(providers)} context provider plugins")
        return providers

    def get_filter_providers(self, enabled_patterns: list[str]) -> list[FilterProviderPlugin]:
        """Get enabled plugins that implement FilterProviderPlugin.

        :param enabled_patterns: List of enabled plugin patterns
        :type enabled_patterns: list[str]
        :returns: List of enabled filter provider plugins
        :rtype: list[FilterProviderPlugin]
        """
        enabled = self.get_enabled_plugins(enabled_patterns)

        providers = [p for p in enabled if isinstance(p, FilterProviderPlugin)]

        logger.debug(f"Found {len(providers)} filter provider plugins")
        return providers

    def aggregate_context(self, scope: MergedScope, enabled_patterns: list[str]) -> dict[str, Any]:
        """Aggregate context from all enabled and available plugins.

        :param scope: Merged scope for context
        :type scope: MergedScope
        :param enabled_patterns: List of enabled plugin patterns
        :type enabled_patterns: list[str]
        :returns: Aggregated context dictionary
        :rtype: dict[str, Any]
        :raises PluginExecutionError: If plugin execution fails
        """
        context: dict[str, Any] = {}

        providers = self.get_context_providers(enabled_patterns)

        for plugin in providers:
            try:
                if not plugin.is_available():
                    logger.debug(
                        f"Plugin '{plugin.name}' not available in current environment, skipping"
                    )
                    continue

                logger.debug(f"Executing plugin '{plugin.name}'")
                plugin_context = plugin.get_context(scope)

                conflicts = set(context.keys()) & set(plugin_context.keys())
                if conflicts:
                    logger.warning(
                        f"Plugin '{plugin.name}' context conflicts with existing keys: "
                        f"{conflicts}. Plugin values will override."
                    )

                context.update(plugin_context)
                logger.info(
                    f"Plugin '{plugin.name}' contributed {len(plugin_context)} context variables"
                )

            except Exception as e:
                if isinstance(e, PluginExecutionError):
                    raise

                logger.error(f"Plugin '{plugin.name}' execution failed: {e}")
                raise PluginExecutionError(
                    plugin_name=plugin.name, message=str(e), original_error=e
                ) from e

        logger.info(f"Aggregated context from {len(providers)} plugins: {len(context)} variables")
        return context

    def aggregate_filters_and_tests(
        self, enabled_patterns: list[str]
    ) -> tuple[dict[str, Callable], dict[str, Callable]]:
        """Aggregate Jinja2 filters and tests from all enabled filter provider plugins.

        :param enabled_patterns: List of enabled plugin patterns
        :type enabled_patterns: list[str]
        :returns: Tuple of (filters dict, tests dict)
        :rtype: tuple[dict[str, Callable], dict[str, Callable]]
        :raises PluginExecutionError: If plugin execution fails
        """
        filters: dict[str, Callable] = {}
        tests: dict[str, Callable] = {}

        providers = self.get_filter_providers(enabled_patterns)

        for plugin in providers:
            try:
                if not plugin.is_available():
                    logger.debug(
                        f"Plugin '{plugin.name}' not available in current environment, skipping"
                    )
                    continue

                logger.debug(f"Getting filters/tests from plugin '{plugin.name}'")

                plugin_filters = plugin.get_filters()
                plugin_tests = plugin.get_tests()

                # Check for conflicts in filters
                filter_conflicts = set(filters.keys()) & set(plugin_filters.keys())
                if filter_conflicts:
                    logger.warning(
                        f"Plugin '{plugin.name}' filters conflict with existing: "
                        f"{filter_conflicts}. Plugin filters will override."
                    )

                # Check for conflicts in tests
                test_conflicts = set(tests.keys()) & set(plugin_tests.keys())
                if test_conflicts:
                    logger.warning(
                        f"Plugin '{plugin.name}' tests conflict with existing: "
                        f"{test_conflicts}. Plugin tests will override."
                    )

                filters.update(plugin_filters)
                tests.update(plugin_tests)

                logger.info(
                    f"Plugin '{plugin.name}' contributed {len(plugin_filters)} filters "
                    f"and {len(plugin_tests)} tests"
                )

            except Exception as e:
                if isinstance(e, PluginExecutionError):
                    raise

                logger.error(f"Plugin '{plugin.name}' filter/test registration failed: {e}")
                raise PluginExecutionError(
                    plugin_name=plugin.name, message=str(e), original_error=e
                ) from e

        logger.info(
            f"Aggregated {len(filters)} filters and {len(tests)} tests "
            f"from {len(providers)} plugins"
        )
        return filters, tests

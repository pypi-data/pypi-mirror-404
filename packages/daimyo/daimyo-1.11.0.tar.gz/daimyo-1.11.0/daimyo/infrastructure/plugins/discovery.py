"""Plugin discovery via Python entry points."""

from collections.abc import Iterator
from importlib.metadata import entry_points

from daimyo.domain import (
    BasePlugin,
    ContextProviderPlugin,
    FilterProviderPlugin,
    PluginExecutionError,
)
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PluginDiscoveryService:
    """Discovers plugins via Python entry points."""

    ENTRY_POINT_GROUP = "daimyo.plugins"

    def discover_all(self) -> Iterator[BasePlugin]:
        """Discover all registered plugins.

        :returns: Iterator of plugin instances
        :rtype: Iterator[BasePlugin]
        :raises PluginExecutionError: If plugin instantiation fails
        """
        logger.info(f"Discovering plugins in entry point group: {self.ENTRY_POINT_GROUP}")

        discovered_count = 0
        eps = entry_points()

        if hasattr(eps, "select"):
            plugin_eps = eps.select(group=self.ENTRY_POINT_GROUP)
        else:
            plugin_eps = eps.get(self.ENTRY_POINT_GROUP, [])  # type: ignore[arg-type]

        for ep in plugin_eps:
            try:
                logger.debug(f"Loading plugin entry point: {ep.name}")
                plugin_class = ep.load()
                plugin_instance = plugin_class()

                if not isinstance(plugin_instance, BasePlugin):
                    logger.warning(f"Plugin {ep.name} does not inherit from BasePlugin, skipping")
                    continue

                # Log plugin type
                plugin_type = "base"
                if isinstance(plugin_instance, ContextProviderPlugin):
                    plugin_type = "context provider"
                if isinstance(plugin_instance, FilterProviderPlugin):
                    if plugin_type != "base":
                        plugin_type = f"{plugin_type} + filter provider"
                    else:
                        plugin_type = "filter provider"

                discovered_count += 1
                logger.info(
                    f"Discovered {plugin_type} plugin: {plugin_instance.name} - "
                    f"{plugin_instance.description}"
                )
                yield plugin_instance

            except Exception as e:
                logger.error(f"Failed to load plugin {ep.name}: {e}")
                raise PluginExecutionError(
                    plugin_name=ep.name,
                    message="Plugin instantiation failed",
                    original_error=e,
                ) from e

        logger.info(f"Plugin discovery complete: {discovered_count} plugins discovered")

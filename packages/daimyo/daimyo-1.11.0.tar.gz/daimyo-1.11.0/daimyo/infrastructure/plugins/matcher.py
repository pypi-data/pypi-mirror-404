"""Wildcard pattern matching for plugin enablement."""

import fnmatch
from collections.abc import Sequence

from daimyo.domain import PluginConfigurationError
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class WildcardMatcher:
    """Matches plugin names against wildcard patterns."""

    def __init__(self, patterns: Sequence[str]):
        """Initialize with list of patterns.

        :param patterns: List of wildcard patterns
        :type patterns: Sequence[str]
        :raises PluginConfigurationError: If "*" wildcard is used
        """
        if "*" in patterns:
            raise PluginConfigurationError(
                "Wildcard '*' is not allowed. Please specify explicit plugin patterns."
            )

        self.patterns = list(patterns)
        logger.debug(f"Initialized WildcardMatcher with patterns: {self.patterns}")

    def matches(self, plugin_name: str) -> bool:
        """Check if plugin name matches any pattern.

        :param plugin_name: Plugin name to check
        :type plugin_name: str
        :returns: True if plugin matches at least one pattern
        :rtype: bool
        """
        for pattern in self.patterns:
            if fnmatch.fnmatch(plugin_name, pattern):
                logger.debug(f"Plugin '{plugin_name}' matched pattern '{pattern}'")
                return True

        logger.debug(f"Plugin '{plugin_name}' did not match any patterns")
        return False

    def filter_plugins(self, plugin_names: Sequence[str]) -> list[str]:
        """Filter plugin names by patterns.

        :param plugin_names: List of plugin names
        :type plugin_names: Sequence[str]
        :returns: Filtered list of matching plugin names
        :rtype: list[str]
        """
        return [name for name in plugin_names if self.matches(name)]

"""Nested dictionary navigation utilities for formatters."""

from typing import Any

from daimyo.domain import CategoryKey


class NestedDictNavigator:
    """Utility for building nested dictionaries from category key paths.

    This is a static utility class (not a mixin) that provides helper methods
    for formatters that need to create nested dictionary structures based on
    CategoryKey paths.
    """

    @staticmethod
    def navigate_and_set(
        root: dict[str, Any],
        key: CategoryKey,
        value: Any,
    ) -> None:
        """Navigate category key path and set value at leaf.

        Creates intermediate dictionaries as needed and sets the final
        value at the leaf position of the path.

        Example:
            root = {}
            key = CategoryKey.from_string("python.web.api")
            value = {"when": "...", "ruleset": [...]}
            navigate_and_set(root, key, value)

        :param root: Root dictionary to navigate
        :type root: dict[str, Any]
        :param key: Category key defining the path
        :type key: CategoryKey
        :param value: Value to set at leaf
        :type value: Any
        :rtype: None
        """
        parts = key.parts
        current = root

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]


__all__ = ["NestedDictNavigator"]

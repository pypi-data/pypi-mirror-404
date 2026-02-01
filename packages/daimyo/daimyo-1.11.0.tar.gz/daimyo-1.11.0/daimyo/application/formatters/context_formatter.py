"""Formatters for displaying template context."""

from __future__ import annotations

import json
from typing import Any

import yaml  # type: ignore[import-untyped]


class ContextYamlFormatter:
    """Format template context as YAML with optional source annotations."""

    def __init__(self, show_sources: bool = False):
        """Initialize formatter.

        :param show_sources: Whether to show source annotations as comments
        :type show_sources: bool
        """
        self.show_sources = show_sources

    def format(
        self,
        context_data: dict[str, dict[str, Any]],
        scope_name: str,
        category_name: str | None,
        filters: dict[str, Any],
        tests: dict[str, Any],
    ) -> str:
        """Format context as YAML.

        :param context_data: Context organized by source
        :type context_data: dict[str, dict[str, Any]]
        :param scope_name: Name of the scope
        :type scope_name: str
        :param category_name: Optional category name
        :type category_name: str | None
        :param filters: Plugin filters
        :type filters: dict[str, Any]
        :param tests: Plugin tests
        :type tests: dict[str, Any]
        :returns: Formatted YAML string
        :rtype: str
        """
        lines = []

        lines.append(f"# Template Context for scope: {scope_name}")
        if category_name:
            lines.append(f"# Category: {category_name}")
        lines.append("")

        for section_name in ["config", "scope", "category", "plugins"]:
            if section_name not in context_data:
                continue

            section_data = context_data[section_name]
            if not section_data:
                continue

            lines.append(f"{section_name}:")
            yaml_str = yaml.dump(
                section_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            for line in yaml_str.strip().split("\n"):
                lines.append(f"  {line}")
            lines.append("")

        if filters or tests:
            lines.append("# Plugin Metadata")
            lines.append("")

        if filters:
            filter_names = list(filters.keys())
            lines.append(f"# Filters Available ({len(filter_names)}):")
            for name in sorted(filter_names):
                lines.append(f"#   - {name}")
            lines.append("")

        if tests:
            test_names = list(tests.keys())
            lines.append(f"# Tests Available ({len(test_names)}):")
            for name in sorted(test_names):
                lines.append(f"#   - {name}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


class ContextJsonFormatter:
    """Format template context as JSON."""

    def __init__(self, show_sources: bool = False):
        """Initialize formatter.

        :param show_sources: Whether to include source information
        :type show_sources: bool
        """
        self.show_sources = show_sources

    def format(
        self,
        context_data: dict[str, dict[str, Any]],
        scope_name: str,
        category_name: str | None,
        filters: dict[str, Any],
        tests: dict[str, Any],
    ) -> str:
        """Format context as JSON.

        :param context_data: Context organized by source
        :type context_data: dict[str, dict[str, Any]]
        :param scope_name: Name of the scope
        :type scope_name: str
        :param category_name: Optional category name
        :type category_name: str | None
        :param filters: Plugin filters
        :type filters: dict[str, Any]
        :param tests: Plugin tests
        :type tests: dict[str, Any]
        :returns: Formatted JSON string
        :rtype: str
        """
        output: dict[str, Any] = {
            "scope_name": scope_name,
            "context": {},
            "metadata": {},
        }

        if category_name:
            output["category"] = category_name

        for section_name, section_data in context_data.items():
            if section_data:
                output["context"][section_name] = section_data

        if filters:
            output["metadata"]["filters"] = sorted(filters.keys())

        if tests:
            output["metadata"]["tests"] = sorted(tests.keys())

        return json.dumps(output, indent=2, ensure_ascii=False) + "\n"


class ContextTableFormatter:
    """Format template context as a table."""

    def __init__(self, show_sources: bool = False):
        """Initialize formatter.

        :param show_sources: Whether to show source column
        :type show_sources: bool
        """
        self.show_sources = show_sources

    def format(
        self,
        context_data: dict[str, dict[str, Any]],
        scope_name: str,
        category_name: str | None,
        filters: dict[str, Any],
        tests: dict[str, Any],
    ) -> str:
        """Format context as a table.

        :param context_data: Context organized by source
        :type context_data: dict[str, dict[str, Any]]
        :param scope_name: Name of the scope
        :type scope_name: str
        :param category_name: Optional category name
        :type category_name: str | None
        :param filters: Plugin filters
        :type filters: dict[str, Any]
        :param tests: Plugin tests
        :type tests: dict[str, Any]
        :returns: Formatted table string
        :rtype: str
        """
        lines = []

        lines.append(f"Template Context for scope: {scope_name}")
        if category_name:
            lines.append(f"Category: {category_name}")
        lines.append("")

        for section_name in ["config", "scope", "category", "plugins"]:
            if section_name not in context_data:
                continue

            section_data = context_data[section_name]
            if not section_data:
                continue

            lines.append(f"{section_name.upper()}:")
            lines.append("")

            self._format_section_table(lines, section_data, section_name)
            lines.append("")

        if filters or tests:
            lines.append("PLUGIN METADATA:")
            lines.append("")

            if filters:
                filter_names = sorted(filters.keys())
                lines.append(f"Filters Available ({len(filter_names)}):")
                lines.append("  " + ", ".join(filter_names))
                lines.append("")

            if tests:
                test_names = sorted(tests.keys())
                lines.append(f"Tests Available ({len(test_names)}):")
                lines.append("  " + ", ".join(test_names))
                lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def _format_section_table(
        self,
        lines: list[str],
        data: dict[str, Any],
        source: str,
    ) -> None:
        """Format a section as table rows.

        :param lines: Lines list to append to
        :type lines: list[str]
        :param data: Section data
        :type data: dict[str, Any]
        :param source: Source name for annotations
        :type source: str
        :rtype: None
        """
        items: list[tuple[str, Any]] = []
        self._flatten_dict(data, "", items)

        if not items:
            lines.append("  (empty)")
            return

        max_key_len = max(len(key) for key, _ in items)
        max_key_len = min(max_key_len, 40)

        for key, value in items:
            value_str = self._format_value(value)
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."

            if self.show_sources:
                lines.append(f"  {key:<{max_key_len}} = {value_str:<60} [{source}]")
            else:
                lines.append(f"  {key:<{max_key_len}} = {value_str}")

    def _flatten_dict(
        self,
        data: Any,
        prefix: str,
        items: list[tuple[str, Any]],
    ) -> None:
        """Flatten nested dictionary into key-value pairs.

        :param data: Data to flatten
        :type data: Any
        :param prefix: Key prefix
        :type prefix: str
        :param items: List to append items to
        :type items: list[tuple[str, Any]]
        :rtype: None
        """
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    self._flatten_dict(value, full_key, items)
                else:
                    items.append((full_key, value))
        else:
            items.append((prefix, data))

    def _format_value(self, value: Any) -> str:
        """Format a value for display.

        :param value: Value to format
        :type value: Any
        :returns: Formatted string
        :rtype: str
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (list, tuple)):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, str):
            return value
        else:
            return str(value)


def get_context_formatter(format: str, show_sources: bool) -> Any:
    """Get formatter instance based on format string.

    :param format: Format name: yaml, json, or table
    :type format: str
    :param show_sources: Whether to show source annotations
    :type show_sources: bool
    :returns: Formatter instance
    :rtype: Any
    :raises ValueError: If format is unknown
    """
    if format == "yaml":
        return ContextYamlFormatter(show_sources=show_sources)
    elif format == "json":
        return ContextJsonFormatter(show_sources=show_sources)
    elif format == "table":
        return ContextTableFormatter(show_sources=show_sources)
    else:
        raise ValueError(f"Unknown format: {format}")


__all__ = [
    "ContextYamlFormatter",
    "ContextJsonFormatter",
    "ContextTableFormatter",
    "get_context_formatter",
]

"""Category string parser for filtering."""

from __future__ import annotations


class CategoryStringParser:
    """Parser for comma-separated category filter strings."""

    @staticmethod
    def parse(categories: str | None) -> list[str]:
        """Parse comma-separated category string into list.

        :param categories: Comma-separated category string (e.g., "python.web,python.testing")
        :type categories: str | None
        :returns: List of category filters, empty list if None or empty
        :rtype: list[str]

        Examples::

            >>> CategoryStringParser.parse("python.web,python.testing")
            ['python.web', 'python.testing']

            >>> CategoryStringParser.parse("  python.web  , python.testing  ")
            ['python.web', 'python.testing']

            >>> CategoryStringParser.parse(None)
            []

            >>> CategoryStringParser.parse("")
            []
        """
        if not categories:
            return []
        return [c.strip() for c in categories.split(",") if c.strip()]


__all__ = ["CategoryStringParser"]

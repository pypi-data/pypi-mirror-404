"""Category filtering service for scopes."""

from __future__ import annotations

from daimyo.application.filtering.category_parser import CategoryStringParser
from daimyo.application.rule_service import RuleMergingService
from daimyo.domain import MergedScope
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CategoryFilterService:
    """Service for filtering categories in scopes."""

    def __init__(self, rule_service: RuleMergingService):
        """Initialize category filter service.

        :param rule_service: Rule merging service for filtering
        :type rule_service: RuleMergingService
        """
        self.rule_service = rule_service
        self.parser = CategoryStringParser()

    def apply_filters(self, scope: MergedScope, category_filters: list[str] | None) -> MergedScope:
        """Apply category filters to a merged scope.

        Filters both commandments and suggestions by the given category prefixes.
        If no filters provided, returns scope unchanged.

        :param scope: Merged scope to filter
        :type scope: MergedScope
        :param category_filters: List of category prefix filters
        :type category_filters: list[str] | None
        :returns: Scope with filtered categories
        :rtype: MergedScope
        """
        if not category_filters:
            return scope

        logger.debug(f"Filtering scope by categories: {category_filters}")

        filtered_scope = scope.copy()
        filtered_scope.commandments = self.rule_service.filter_categories(
            filtered_scope.commandments, category_filters
        )
        filtered_scope.suggestions = self.rule_service.filter_categories(
            filtered_scope.suggestions, category_filters
        )

        return filtered_scope

    def filter_from_string(self, scope: MergedScope, categories: str | None) -> MergedScope:
        """Parse category string and apply filters to scope.

        Convenience method combining category parsing and filter application.

        :param scope: Merged scope to filter
        :type scope: MergedScope
        :param categories: Comma-separated category string
        :type categories: str | None
        :returns: Scope with filtered categories
        :rtype: MergedScope
        """
        category_list = self.parser.parse(categories)
        return self.apply_filters(scope, category_list)


__all__ = ["CategoryFilterService"]

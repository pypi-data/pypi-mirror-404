"""Tests for CategoryFilterService."""

from __future__ import annotations

import pytest

from daimyo.application.filtering.category_filter import CategoryFilterService
from daimyo.application.rule_service import RuleMergingService
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


@pytest.fixture
def rule_service() -> RuleMergingService:
    """Create a rule merging service."""
    return RuleMergingService()


@pytest.fixture
def filter_service(rule_service: RuleMergingService) -> CategoryFilterService:
    """Create a category filter service."""
    return CategoryFilterService(rule_service)


@pytest.fixture
def sample_scope() -> MergedScope:
    """Create a sample merged scope with multiple categories."""
    commandments = RuleSet()

    # Add testing category
    testing_cat = Category(key=CategoryKey.from_string("testing"))
    testing_cat.add_rule(Rule(text="Write unit tests", rule_type=RuleType.COMMANDMENT))
    testing_cat.add_rule(Rule(text="Write integration tests", rule_type=RuleType.COMMANDMENT))
    commandments.add_category(testing_cat)

    # Add documentation category
    docs_cat = Category(key=CategoryKey.from_string("documentation"))
    docs_cat.add_rule(Rule(text="Write API documentation", rule_type=RuleType.COMMANDMENT))
    commandments.add_category(docs_cat)

    # Add code-style category
    style_cat = Category(key=CategoryKey.from_string("code-style"))
    style_cat.add_rule(Rule(text="Follow PEP 8", rule_type=RuleType.COMMANDMENT))
    commandments.add_category(style_cat)

    suggestions = RuleSet()
    perf_cat = Category(key=CategoryKey.from_string("performance"))
    perf_cat.add_rule(Rule(text="Profile before optimizing", rule_type=RuleType.SUGGESTION))
    suggestions.add_category(perf_cat)

    return MergedScope(
        metadata=ScopeMetadata(name="test-scope", description="Test scope"),
        commandments=commandments,
        suggestions=suggestions,
        sources=["local"],
    )


class TestCategoryFilterService:
    """Tests for CategoryFilterService."""

    def test_apply_filters_no_filters_returns_unchanged(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test that no filters returns the scope unchanged."""
        result = filter_service.apply_filters(sample_scope, None)
        assert result is sample_scope

    def test_apply_filters_single_category(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test filtering to a single category."""
        result = filter_service.apply_filters(sample_scope, ["testing"])

        assert len(result.commandments.categories) == 1
        assert CategoryKey.from_string("testing") in result.commandments.categories
        assert len(result.commandments.categories[CategoryKey.from_string("testing")].rules) == 2

    def test_apply_filters_multiple_categories(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test filtering to multiple categories."""
        result = filter_service.apply_filters(sample_scope, ["testing", "documentation"])

        assert len(result.commandments.categories) == 2
        assert CategoryKey.from_string("testing") in result.commandments.categories
        assert CategoryKey.from_string("documentation") in result.commandments.categories
        assert CategoryKey.from_string("code-style") not in result.commandments.categories

    def test_apply_filters_empty_category_returns_empty(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test filtering to a non-existent category returns empty rulesets."""
        result = filter_service.apply_filters(sample_scope, ["nonexistent"])

        assert len(result.commandments.categories) == 0
        assert len(result.suggestions.categories) == 0

    def test_apply_filters_does_not_mutate_original(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test that filtering does not mutate the original scope.

        This is critical for cached scopes - filtering should create a new scope
        rather than modifying the cached one.
        """
        original_commandments_count = len(sample_scope.commandments.categories)
        original_suggestions_count = len(sample_scope.suggestions.categories)

        result = filter_service.apply_filters(sample_scope, ["testing"])

        assert len(sample_scope.commandments.categories) == original_commandments_count
        assert len(sample_scope.suggestions.categories) == original_suggestions_count

        assert result is not sample_scope
        assert len(result.commandments.categories) == 1

    def test_apply_filters_multiple_times_with_different_filters(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test that applying different filters multiple times works correctly.

        This simulates the bug scenario where:
        1. First request gets all rules
        2. Second request filters to empty category
        3. Third request should still get results based on its filter
        """
        result1 = filter_service.apply_filters(sample_scope, ["testing"])
        assert len(result1.commandments.categories) == 1
        assert CategoryKey.from_string("testing") in result1.commandments.categories

        result2 = filter_service.apply_filters(sample_scope, ["nonexistent"])
        assert len(result2.commandments.categories) == 0

        result3 = filter_service.apply_filters(sample_scope, ["documentation"])
        assert len(result3.commandments.categories) == 1
        assert CategoryKey.from_string("documentation") in result3.commandments.categories

        assert len(sample_scope.commandments.categories) == 3

    def test_filter_from_string_parses_and_filters(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test that filter_from_string correctly parses and applies filters."""
        result = filter_service.filter_from_string(sample_scope, "testing,documentation")

        assert len(result.commandments.categories) == 2
        assert CategoryKey.from_string("testing") in result.commandments.categories
        assert CategoryKey.from_string("documentation") in result.commandments.categories

    def test_filter_from_string_none_returns_unchanged(
        self, filter_service: CategoryFilterService, sample_scope: MergedScope
    ) -> None:
        """Test that filter_from_string with None returns unchanged scope."""
        result = filter_service.filter_from_string(sample_scope, None)
        assert result is sample_scope

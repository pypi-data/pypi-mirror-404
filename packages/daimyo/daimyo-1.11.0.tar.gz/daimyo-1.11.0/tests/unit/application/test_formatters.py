"""Tests for output formatters."""

import yaml

from daimyo.application.formatters import (
    IndexMarkdownFormatter,
    JsonFormatter,
    MarkdownFormatter,
    YamlMultiDocFormatter,
)
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


class TestYamlMultiDocFormatter:
    """Tests for YAML multi-document formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic YAML multi-doc formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = YamlMultiDocFormatter()
        result = formatter.format(merged)

        documents = list(yaml.safe_load_all(result))
        assert len(documents) == 3

        assert "metadata" in documents[0]
        assert documents[0]["metadata"]["name"] == "test-scope"

        assert "commandments" in documents[1]

        assert "suggestions" in documents[2]


class TestJsonFormatter:
    """Tests for JSON formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic JSON formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = JsonFormatter()
        result = formatter.format(merged)

        assert "metadata" in result
        assert "commandments" in result
        assert "suggestions" in result
        assert result["metadata"]["name"] == "test-scope"


class TestMarkdownFormatter:
    """Tests for Markdown formatter."""

    def test_format_basic(self, sample_scope):
        """Test basic Markdown formatting."""
        from daimyo.domain import MergedScope

        merged = MergedScope.from_scope(sample_scope)
        formatter = MarkdownFormatter()
        result = formatter.format(merged)

        assert "# Rules for test-scope" in result
        assert "## python" in result
        assert "MUST" in result

    def test_format_with_hierarchy(self):
        """Test Markdown formatting with hierarchy."""
        metadata = ScopeMetadata(name="test", description="Test")
        merged = MergedScope(
            metadata=metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        cat1 = Category(CategoryKey.from_string("python"), when="Python")
        cat1.add_rule(Rule("Rule 1", RuleType.COMMANDMENT))
        merged.commandments.add_category(cat1)

        cat2 = Category(CategoryKey.from_string("python.web"), when="Web")
        cat2.add_rule(Rule("Rule 2", RuleType.COMMANDMENT))
        merged.commandments.add_category(cat2)

        formatter = MarkdownFormatter()
        result = formatter.format(merged)

        assert "## python" in result
        assert "### web" in result
        assert "MUST" in result


class TestIndexMarkdownFormatter:
    """Tests for Index Markdown formatter."""

    def test_format_basic(self, sample_merged_scope):
        """Test basic index markdown formatting."""
        formatter = IndexMarkdownFormatter()
        result = formatter.format(sample_merged_scope)

        assert "# Index of rule categories for scope test-scope" in result
        assert "Test scope for unit tests" in result
        assert "When requesting rules" in result

    def test_format_with_footer(self, sample_merged_scope):
        """Test that footer is included by default."""
        formatter = IndexMarkdownFormatter(include_footer=True)
        result = formatter.format(sample_merged_scope)

        expected_text = (
            "When requesting rules, the rules of a given category include "
            "also the rules of all its subcategories."
        )
        assert expected_text in result

    def test_format_without_footer(self, sample_merged_scope):
        """Test that footer can be excluded."""
        formatter = IndexMarkdownFormatter(include_footer=False)
        result = formatter.format(sample_merged_scope)

        assert "When requesting rules" not in result

    def test_format_with_hierarchy(self):
        """Test index formatting with hierarchical categories."""
        metadata = ScopeMetadata(name="test", description="Test scope")
        merged_commandments = RuleSet()
        merged_suggestions = RuleSet()

        python_cat = Category(
            CategoryKey.from_string("python"), when="When writing Python code"
        )
        python_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        merged_commandments.add_category(python_cat)

        web_cat = Category(
            CategoryKey.from_string("python.web"), when="When building web applications"
        )
        web_cat.add_rule(Rule("Use FastAPI", RuleType.COMMANDMENT))
        merged_commandments.add_category(web_cat)

        api_cat = Category(CategoryKey.from_string("python.web.api"), when="When building APIs")
        api_cat.add_rule(Rule("Use REST", RuleType.SUGGESTION))
        merged_suggestions.add_category(api_cat)

        merged_scope = MergedScope(
            metadata=metadata,
            commandments=merged_commandments,
            suggestions=merged_suggestions,
            sources=["local"],
        )

        formatter = IndexMarkdownFormatter(include_footer=False)
        result = formatter.format(merged_scope)

        assert "- `python`: When writing Python code" in result
        assert "  - `python.web`: When building web applications" in result
        assert "    - `python.web.api`: When building APIs" in result

    def test_format_with_empty_categories(self):
        """Test index formatting with no categories."""
        metadata = ScopeMetadata(name="empty", description="Empty scope")
        merged_scope = MergedScope(
            metadata=metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        formatter = IndexMarkdownFormatter()
        result = formatter.format(merged_scope)

        assert "# Index of rule categories for scope empty" in result
        assert "Empty scope" in result

    def test_format_aggregates_categories(self):
        """Test that categories from both commandments and suggestions are aggregated."""
        metadata = ScopeMetadata(name="test", description="Test")
        merged_commandments = RuleSet()
        merged_suggestions = RuleSet()

        cat1 = Category(CategoryKey.from_string("python"), when="Python code")
        cat1.add_rule(Rule("Rule 1", RuleType.COMMANDMENT))
        merged_commandments.add_category(cat1)

        cat2 = Category(CategoryKey.from_string("python.web"), when="Web development")
        cat2.add_rule(Rule("Rule 2", RuleType.SUGGESTION))
        merged_suggestions.add_category(cat2)

        merged_scope = MergedScope(
            metadata=metadata,
            commandments=merged_commandments,
            suggestions=merged_suggestions,
            sources=["local"],
        )

        formatter = IndexMarkdownFormatter(include_footer=False)
        result = formatter.format(merged_scope)

        assert "- `python`: Python code" in result
        assert "  - `python.web`: Web development" in result

    def test_format_backtick_formatting(self, sample_merged_scope):
        """Test that category keys are wrapped in backticks."""
        formatter = IndexMarkdownFormatter()
        result = formatter.format(sample_merged_scope)

        assert "`python`" in result
        assert "`python.testing`" in result

    def test_format_no_description(self):
        """Test formatting when scope has no description."""
        metadata = ScopeMetadata(name="no-desc", description=None)
        merged_scope = MergedScope(
            metadata=metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        formatter = IndexMarkdownFormatter()
        result = formatter.format(merged_scope)

        assert "# Index of rule categories for scope no-desc" in result
        lines = result.split("\n")
        assert lines[0] == "# Index of rule categories for scope no-desc"


__all__ = [
    "TestYamlMultiDocFormatter",
    "TestJsonFormatter",
    "TestMarkdownFormatter",
    "TestIndexMarkdownFormatter",
]

"""Tests for formatter helper mixins and utilities."""

from unittest.mock import Mock

from daimyo.application.formatters.helpers import (
    MetadataBuilderMixin,
    NestedDictNavigator,
    RuleProcessorMixin,
    TemplateAwareMixin,
)
from daimyo.domain import Category, CategoryKey, MergedScope, Rule, RuleSet, RuleType, ScopeMetadata


class TestTemplateAwareMixin:
    """Tests for TemplateAwareMixin."""

    def test_render_text_without_renderer(self):
        """Test that text is returned unchanged when no renderer."""

        class TestFormatter(TemplateAwareMixin):
            def __init__(self):
                self.template_renderer = None

        formatter = TestFormatter()
        scope = MergedScope(
            metadata=ScopeMetadata(name="test", description="Test"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        result = formatter._render_text("Hello {{ name }}", scope)
        assert result == "Hello {{ name }}"

    def test_render_text_with_renderer(self):
        """Test that renderer is called when available."""

        class TestFormatter(TemplateAwareMixin):
            def __init__(self, renderer):
                self.template_renderer = renderer

        mock_renderer = Mock()
        mock_renderer.render_rule_text.return_value = "Rendered text"

        formatter = TestFormatter(mock_renderer)
        scope = MergedScope(
            metadata=ScopeMetadata(name="test", description="Test"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )
        category = Category(CategoryKey.from_string("python"), when="Python")

        result = formatter._render_text("Template", scope, category)

        assert result == "Rendered text"
        mock_renderer.render_rule_text.assert_called_once_with(
            "Template", scope, category, None, None
        )


class TestRuleProcessorMixin:
    """Tests for RuleProcessorMixin."""

    def test_render_and_prune_rules(self):
        """Test rule rendering and pruning."""

        class TestFormatter(TemplateAwareMixin, RuleProcessorMixin):
            def __init__(self):
                self.template_renderer = None

        formatter = TestFormatter()
        scope = MergedScope(
            metadata=ScopeMetadata(name="test", description="Test"),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local"],
        )

        category = Category(CategoryKey.from_string("python"), when="Python")
        category.add_rule(Rule("Keep this", RuleType.COMMANDMENT))
        category.add_rule(Rule("   ", RuleType.COMMANDMENT))
        category.add_rule(Rule("Also keep", RuleType.COMMANDMENT))
        category.add_rule(Rule("", RuleType.COMMANDMENT))

        result = formatter._render_and_prune_rules(category, scope)

        assert len(result) == 2
        assert "Keep this" in result
        assert "Also keep" in result
        assert "   " not in result
        assert "" not in result


class TestMetadataBuilderMixin:
    """Tests for MetadataBuilderMixin."""

    def test_build_metadata_dict(self):
        """Test metadata dict construction."""

        class TestFormatter(MetadataBuilderMixin):
            pass

        formatter = TestFormatter()
        scope = MergedScope(
            metadata=ScopeMetadata(
                name="test-scope",
                description="Test description",
                parent="parent-scope",
                tags={"tag1": "value1", "tag2": "value2"},
            ),
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=["local", "remote"],
        )

        result = formatter._build_metadata_dict(scope)

        assert result == {
            "name": "test-scope",
            "description": "Test description",
            "parent": "parent-scope",
            "tags": {"tag1": "value1", "tag2": "value2"},
            "sources": ["local", "remote"],
        }


class TestNestedDictNavigator:
    """Tests for NestedDictNavigator."""

    def test_navigate_and_set_single_level(self):
        """Test navigation with single-level key."""
        root = {}
        key = CategoryKey.from_string("python")
        value = {"data": "test"}

        NestedDictNavigator.navigate_and_set(root, key, value)

        assert root == {"python": {"data": "test"}}

    def test_navigate_and_set_nested(self):
        """Test navigation with multi-level key."""
        root = {}
        key = CategoryKey.from_string("python.web.api")
        value = {"when": "APIs", "ruleset": ["rule1"]}

        NestedDictNavigator.navigate_and_set(root, key, value)

        assert root == {
            "python": {
                "web": {
                    "api": {"when": "APIs", "ruleset": ["rule1"]}
                }
            }
        }

    def test_navigate_and_set_existing_path(self):
        """Test navigation when intermediate dicts already exist."""
        root = {"python": {"web": {}}}
        key = CategoryKey.from_string("python.web.api")
        value = {"data": "test"}

        NestedDictNavigator.navigate_and_set(root, key, value)

        assert root == {
            "python": {
                "web": {
                    "api": {"data": "test"}
                }
            }
        }

    def test_navigate_and_set_multiple_keys(self):
        """Test multiple navigations build correct tree."""
        root = {}

        NestedDictNavigator.navigate_and_set(
            root,
            CategoryKey.from_string("python.web"),
            {"data": "web"}
        )
        NestedDictNavigator.navigate_and_set(
            root,
            CategoryKey.from_string("python.testing"),
            {"data": "test"}
        )
        NestedDictNavigator.navigate_and_set(
            root,
            CategoryKey.from_string("javascript"),
            {"data": "js"}
        )

        assert root == {
            "python": {
                "web": {"data": "web"},
                "testing": {"data": "test"},
            },
            "javascript": {"data": "js"},
        }


__all__ = [
    "TestTemplateAwareMixin",
    "TestRuleProcessorMixin",
    "TestMetadataBuilderMixin",
    "TestNestedDictNavigator",
]

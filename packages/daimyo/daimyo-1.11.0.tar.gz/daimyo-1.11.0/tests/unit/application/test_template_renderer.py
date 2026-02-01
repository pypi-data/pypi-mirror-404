"""Tests for template rendering service."""

from unittest.mock import Mock

import pytest

from daimyo.application.templating import TemplateRenderer
from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    RuleSet,
    ScopeMetadata,
    TemplateRenderingError,
)


@pytest.fixture
def mock_settings():
    """Mock Dynaconf settings."""
    settings = Mock()
    settings.as_dict.return_value = {
        "RULES_PATH": "./rules",
        "LOG_LEVEL": "INFO",
        "MY_CUSTOM_VAR": "custom_value",
        "TEAM_NAME": "Backend Team",
        # Exclude complex types
        "_internal_object": object(),
    }
    return settings


@pytest.fixture
def template_renderer(mock_settings):
    """Template renderer with mock settings."""
    return TemplateRenderer(mock_settings)


@pytest.fixture
def sample_scope():
    """Sample merged scope for testing."""
    metadata = ScopeMetadata(
        name="test-scope",
        description="Test scope",
        tags={"team": "backend", "env": "prod"},
    )
    return MergedScope(
        metadata=metadata,
        commandments=RuleSet(),
        suggestions=RuleSet(),
        sources=["local"],
    )


@pytest.fixture
def sample_category():
    """Sample category."""
    return Category(
        key=CategoryKey.from_string("python.testing"),
        when="When writing tests",
    )


class TestTemplateDetection:
    """Test template syntax detection."""

    def test_needs_rendering_with_double_braces(self, template_renderer):
        """Detect {{ }} syntax."""
        assert template_renderer.needs_rendering("Use {{ MY_VAR }} here")
        assert template_renderer.needs_rendering("{{ VAR }}")

    def test_needs_rendering_with_control_structures(self, template_renderer):
        """Detect {% %} syntax."""
        assert template_renderer.needs_rendering("{% if VAR %}text{% endif %}")

    def test_needs_rendering_plain_text(self, template_renderer):
        """Plain text without templates."""
        assert not template_renderer.needs_rendering("Plain rule text")
        assert not template_renderer.needs_rendering("Use curly braces { } but not templates")


class TestBasicRendering:
    """Test basic template rendering."""

    def test_render_config_variable(self, template_renderer, sample_scope):
        """Render configuration variable."""
        text = "Rules are stored in {{ RULES_PATH }}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "Rules are stored in ./rules"

    def test_render_scope_metadata(self, template_renderer, sample_scope):
        """Render scope metadata."""
        text = "Scope: {{ scope.name }}, Team: {{ scope.tags.team }}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "Scope: test-scope, Team: backend"

    def test_render_category_info(self, template_renderer, sample_scope, sample_category):
        """Render category information."""
        text = "Category {{ category.key }} applies {{ category.when }}"
        result = template_renderer.render_rule_text(text, sample_scope, sample_category)
        assert result == "Category python.testing applies When writing tests"

    def test_render_plain_text_unchanged(self, template_renderer, sample_scope):
        """Plain text passes through unchanged."""
        text = "No templates here"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "No templates here"


class TestDefaultFilter:
    """Test Jinja2 default filter for optional variables."""

    def test_default_filter_with_undefined_var(self, template_renderer, sample_scope):
        """Use default filter for undefined variable."""
        text = "Value: {{ UNDEFINED_VAR | default('fallback') }}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "Value: fallback"

    def test_default_filter_with_defined_var(self, template_renderer, sample_scope):
        """Default filter doesn't override defined value."""
        text = "Path: {{ RULES_PATH | default('/default/path') }}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "Path: ./rules"


class TestStrictUndefined:
    """Test strict undefined variable checking."""

    def test_undefined_variable_raises_error(self, template_renderer, sample_scope):
        """Undefined variable raises TemplateRenderingError."""
        text = "Use {{ UNDEFINED_VARIABLE }} here"

        with pytest.raises(TemplateRenderingError) as exc_info:
            template_renderer.render_rule_text(text, sample_scope)

        error = exc_info.value
        assert error.variable_name == "UNDEFINED_VARIABLE"
        assert "UNDEFINED_VARIABLE" in str(error)
        assert "default" in str(error).lower()  # Error message suggests default filter

    def test_error_includes_context(self, template_renderer, sample_scope, sample_category):
        """Error message includes scope and category context."""
        text = "{{ MISSING_VAR }}"

        with pytest.raises(TemplateRenderingError) as exc_info:
            template_renderer.render_rule_text(text, sample_scope, sample_category)

        error = exc_info.value
        assert "test-scope" in error.context_info
        assert "python.testing" in error.context_info


class TestCategoryWhenRendering:
    """Test rendering category 'when' descriptions."""

    def test_render_category_when(self, template_renderer, sample_scope, sample_category):
        """Render category when description."""
        when_text = "When testing {{ scope.name }} in {{ scope.tags.env }}"
        result = template_renderer.render_category_when(when_text, sample_scope, sample_category)
        assert result == "When testing test-scope in prod"


class TestContextBuilder:
    """Test context building logic."""

    def test_context_includes_settings(self, template_renderer, sample_scope):
        """Context includes all simple-type settings."""
        context = template_renderer._build_context(sample_scope)

        assert context["RULES_PATH"] == "./rules"
        assert context["LOG_LEVEL"] == "INFO"
        assert context["MY_CUSTOM_VAR"] == "custom_value"
        assert "_internal_object" not in context  # Complex types excluded

    def test_context_includes_scope(self, template_renderer, sample_scope):
        """Context includes scope metadata."""
        context = template_renderer._build_context(sample_scope)

        assert context["scope"]["name"] == "test-scope"
        assert context["scope"]["description"] == "Test scope"
        assert context["scope"]["tags"]["team"] == "backend"
        assert context["scope"]["sources"] == ["local"]

    def test_context_includes_category(self, template_renderer, sample_scope, sample_category):
        """Context includes category when provided."""
        context = template_renderer._build_context(sample_scope, sample_category)

        assert context["category"]["key"] == "python.testing"
        assert context["category"]["when"] == "When writing tests"


class TestComplexTemplates:
    """Test complex template scenarios."""

    def test_multiple_variables(self, template_renderer, sample_scope):
        """Template with multiple variables."""
        text = "{{ scope.name }} uses {{ LOG_LEVEL }} logging at {{ RULES_PATH }}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "test-scope uses INFO logging at ./rules"

    def test_conditional_logic(self, template_renderer, sample_scope):
        """Template with Jinja2 conditionals."""
        text = "{% if scope.tags.env == 'prod' %}Production rules{% else %}Dev rules{% endif %}"
        result = template_renderer.render_rule_text(text, sample_scope)
        assert result == "Production rules"


class TestNonExistentJinja2Test:
    """Test handling of non-existent Jinja2 tests and filters."""

    def test_nonexistent_test_raises_error(self, template_renderer, sample_scope):
        """Non-existent Jinja2 test raises TemplateRenderingError."""
        text = "{% if scope.name is nonexistent_test %}yes{% endif %}"

        with pytest.raises(TemplateRenderingError) as exc_info:
            template_renderer.render_rule_text(text, sample_scope)

        error = exc_info.value
        assert "nonexistent_test" in error.variable_name
        assert "test-scope" in error.context_info

    def test_nonexistent_test_in_category_when_raises_error(
        self, template_renderer, sample_scope, sample_category
    ):
        """Non-existent test in category when description raises error."""
        when_text = "{% if category.key is my_custom_test %}When condition{% endif %}"

        with pytest.raises(TemplateRenderingError) as exc_info:
            template_renderer.render_category_when(when_text, sample_scope, sample_category)

        error = exc_info.value
        assert "my_custom_test" in error.variable_name
        assert "test-scope" in error.context_info
        assert "python.testing" in error.context_info

    def test_nonexistent_test_graceful_mode(self, template_renderer, sample_scope):
        """Non-existent test returns empty string in graceful mode."""
        text = "{% if scope.name is nonexistent_test %}yes{% endif %}"
        result = template_renderer.render_rule_text(
            text, sample_scope, failure_collector=sample_scope
        )

        assert result == ""
        assert len(sample_scope.template_failures) == 1
        failure = sample_scope.template_failures[0]
        assert failure.element_type == "rule"
        assert failure.template_text == text
        assert failure.variable_name is None

    def test_nonexistent_test_in_category_when_graceful_mode(
        self, template_renderer, sample_scope, sample_category
    ):
        """Non-existent test in category when description returns empty in graceful mode."""
        when_text = "{% if category.key is my_test %}When condition{% endif %}"
        result = template_renderer.render_category_when(
            when_text, sample_scope, sample_category, failure_collector=sample_scope
        )

        assert result == ""
        assert len(sample_scope.template_failures) == 1
        failure = sample_scope.template_failures[0]
        assert failure.element_type == "category_when"
        assert "python.testing" in failure.element_identifier
        assert failure.template_text == when_text
        assert failure.variable_name is None

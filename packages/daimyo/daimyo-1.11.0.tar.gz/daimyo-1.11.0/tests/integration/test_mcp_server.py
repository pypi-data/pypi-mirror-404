"""Integration tests for MCP server."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from daimyo.domain import (
    Category,
    CategoryKey,
    MergedScope,
    Rule,
    RuleSet,
    RuleType,
    ScopeMetadata,
    ScopeNotFoundError,
)
from daimyo.presentation.mcp import server


class TestMCPServer:
    """Test suite for MCP server tools."""

    @pytest.fixture
    def sample_merged_scope(self):
        """Create sample merged scope for testing."""
        metadata = ScopeMetadata(
            name="test-scope", description="Test scope", parent=None, tags={"type": "test"}
        )

        commandments = RuleSet()
        cmd_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        cmd_cat.add_rule(Rule("Use type hints", RuleType.COMMANDMENT))
        cmd_cat.add_rule(Rule("Follow PEP 8", RuleType.COMMANDMENT))
        commandments.add_category(cmd_cat)

        suggestions = RuleSet()
        sug_cat = Category(key=CategoryKey.from_string("python"), when="When writing Python")
        sug_cat.add_rule(Rule("Consider dataclasses", RuleType.SUGGESTION))
        suggestions.add_category(sug_cat)

        return MergedScope(
            metadata=metadata,
            commandments=commandments,
            suggestions=suggestions,
            sources=["local"],
        )

    @patch("daimyo.presentation.mcp.server._filter_service")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_success(self, mock_scope_service, mock_filter_service, sample_merged_scope):
        """Test get_rules returns formatted rules."""
        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_filter_service.filter_from_string.return_value = sample_merged_scope

        result = server.get_rules.fn("test-scope")

        assert isinstance(result, str)
        assert "test-scope" in result.lower() or "Test scope" in result
        assert len(result) > 0
        mock_scope_service.resolve_scope.assert_called_once_with("test-scope")

    @patch("daimyo.presentation.mcp.server._filter_service")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_with_categories(
        self, mock_scope_service, mock_filter_service, sample_merged_scope
    ):
        """Test get_rules with category filtering."""
        filtered_scope = MergedScope(
            metadata=sample_merged_scope.metadata,
            commandments=RuleSet(),
            suggestions=RuleSet(),
            sources=sample_merged_scope.sources
        )

        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_filter_service.filter_from_string.return_value = filtered_scope

        result = server.get_rules.fn("test-scope", categories="python.web,python.testing")

        assert isinstance(result, str)
        mock_filter_service.filter_from_string.assert_called_once()

    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_scope_not_found(self, mock_scope_service):
        """Test get_rules handles ScopeNotFoundError."""
        mock_scope_service.resolve_scope.side_effect = ScopeNotFoundError("test-scope")

        result = server.get_rules.fn("nonexistent")

        assert "Scope Error:" in result or "not found" in result.lower()

    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_unexpected_error(self, mock_scope_service):
        """Test get_rules handles unexpected errors."""
        mock_scope_service.resolve_scope.side_effect = Exception("Unexpected error")

        result = server.get_rules.fn("test-scope")

        assert "error" in result.lower()


    @patch("daimyo.presentation.mcp.server.get_rules.fn")
    def test_apply_scope_rules_success(self, mock_get_rules_fn):
        """Test apply_scope_rules prompt template."""
        mock_get_rules_fn.return_value = "# Test Rules\n\nRule 1\nRule 2"

        result = server.apply_scope_rules.fn("test-scope")

        assert isinstance(result, str)
        assert "test-scope" in result
        assert "MUST rules" in result
        assert "SHOULD rules" in result
        mock_get_rules_fn.assert_called_once_with("test-scope", None)

    @patch("daimyo.presentation.mcp.server.get_rules.fn")
    def test_apply_scope_rules_with_categories(self, mock_get_rules_fn):
        """Test apply_scope_rules with category filters."""
        mock_get_rules_fn.return_value = "# Filtered Rules"

        result = server.apply_scope_rules.fn("test-scope", categories="python.web")

        assert isinstance(result, str)
        mock_get_rules_fn.assert_called_once_with("test-scope", "python.web")

    @patch("daimyo.presentation.mcp.server.get_rules.fn")
    def test_apply_scope_rules_error(self, mock_get_rules_fn):
        """Test apply_scope_rules handles errors."""
        mock_get_rules_fn.side_effect = Exception("Error generating prompt")

        result = server.apply_scope_rules.fn("test-scope")

        assert "Error" in result

    def test_mcp_server_instance_exists(self):
        """Test that mcp server instance exists."""
        assert server.mcp is not None
        assert hasattr(server.mcp, "name")

    def test_mcp_tools_are_registered(self):
        """Test that MCP tools are registered."""
        assert hasattr(server, "get_rules")
        assert callable(server.get_rules.fn)

    def test_mcp_prompts_are_registered(self):
        """Test that MCP prompts are registered."""
        assert hasattr(server, "apply_scope_rules")
        assert callable(server.apply_scope_rules.fn)

    @patch("daimyo.presentation.mcp.server._filter_service")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_formatting_includes_commandments(
        self, mock_scope_service, mock_filter_service, sample_merged_scope
    ):
        """Test that get_rules output includes commandments."""
        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_filter_service.filter_from_string.return_value = sample_merged_scope

        result = server.get_rules.fn("test-scope")

        assert "Use type hints" in result or "commandment" in result.lower()

    @patch("daimyo.presentation.mcp.server._filter_service")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_formatting_includes_suggestions(
        self, mock_scope_service, mock_filter_service, sample_merged_scope
    ):
        """Test that get_rules output includes suggestions."""
        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_filter_service.filter_from_string.return_value = sample_merged_scope

        result = server.get_rules.fn("test-scope")

        assert "Consider dataclasses" in result or "suggestion" in result.lower()

    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_category_index(self, mock_scope_service, sample_merged_scope):
        """Test get_category_index returns category index."""
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        result = server.get_category_index.fn("test-scope")

        assert isinstance(result, str)
        assert "Index of rule categories" in result
        assert "test-scope" in result
        assert "python" in result.lower()

    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_category_index_includes_when_description(
        self, mock_scope_service, sample_merged_scope
    ):
        """Test that category index includes 'when' descriptions."""
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        result = server.get_category_index.fn("test-scope")

        assert "When writing Python" in result

    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_category_index_scope_not_found(self, mock_scope_service):
        """Test get_category_index handles ScopeNotFoundError."""
        mock_scope_service.resolve_scope.side_effect = ScopeNotFoundError("test-scope")

        result = server.get_category_index.fn("nonexistent")

        assert "Scope Error:" in result or "not found" in result.lower()

    @patch("daimyo.presentation.mcp.server.settings")
    @patch("daimyo.presentation.mcp.server._filter_service")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_rules_with_default_scope(
        self, mock_scope_service, mock_filter_service, mock_settings, sample_merged_scope
    ):
        """Test get_rules uses default scope when none provided."""
        mock_settings.DEFAULT_SCOPE = "default-scope"
        mock_scope_service.resolve_scope.return_value = sample_merged_scope
        mock_filter_service.filter_from_string.return_value = sample_merged_scope

        result = server.get_rules.fn(None)

        assert isinstance(result, str)
        assert "Note:" in result
        assert "default-scope" in result
        mock_scope_service.resolve_scope.assert_called_once_with("default-scope")

    @patch("daimyo.presentation.mcp.server.settings")
    def test_get_rules_without_scope_and_no_default(self, mock_settings):
        """Test get_rules returns error when no scope provided and no default configured."""
        mock_settings.DEFAULT_SCOPE = ""

        result = server.get_rules.fn(None)

        assert "Error" in result
        assert "no default scope configured" in result.lower()

    @patch("daimyo.presentation.mcp.server.settings")
    @patch("daimyo.presentation.mcp.server._scope_service")
    def test_get_category_index_with_default_scope(
        self, mock_scope_service, mock_settings, sample_merged_scope
    ):
        """Test get_category_index uses default scope when none provided."""
        mock_settings.DEFAULT_SCOPE = "default-scope"
        mock_scope_service.resolve_scope.return_value = sample_merged_scope

        result = server.get_category_index.fn(None)

        assert isinstance(result, str)
        assert "Note:" in result
        assert "default-scope" in result
        mock_scope_service.resolve_scope.assert_called_once_with("default-scope")

    @patch("daimyo.presentation.mcp.server.settings")
    def test_get_category_index_without_scope_and_no_default(self, mock_settings):
        """Test get_category_index error when no scope provided and no default configured."""
        mock_settings.DEFAULT_SCOPE = ""

        result = server.get_category_index.fn(None)

        assert "Error" in result
        assert "no default scope configured" in result.lower()

    @patch("daimyo.presentation.mcp.server.settings")
    @patch("daimyo.presentation.mcp.server.get_rules.fn")
    def test_apply_scope_rules_with_default_scope(self, mock_get_rules_fn, mock_settings):
        """Test apply_scope_rules uses default scope when none provided."""
        mock_settings.DEFAULT_SCOPE = "default-scope"
        mock_get_rules_fn.return_value = "# Test Rules\n\nRule 1\nRule 2"

        result = server.apply_scope_rules.fn(None)

        assert isinstance(result, str)
        assert "default-scope" in result
        mock_get_rules_fn.assert_called_once_with("default-scope", None)

    @patch("daimyo.presentation.mcp.server.settings")
    def test_apply_scope_rules_without_scope_and_no_default(self, mock_settings):
        """Test apply_scope_rules returns error when no scope provided and no default configured."""
        mock_settings.DEFAULT_SCOPE = ""

        result = server.apply_scope_rules.fn(None)

        assert "Error" in result
        assert "no default scope configured" in result.lower()

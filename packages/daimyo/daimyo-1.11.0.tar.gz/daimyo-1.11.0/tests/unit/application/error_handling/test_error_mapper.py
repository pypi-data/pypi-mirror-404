"""Tests for ErrorMapper functionality."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from daimyo.application.error_handling.error_mapper import ErrorMapper
from daimyo.domain.exceptions import (
    DaimyoError,
    InvalidScopeError,
    RemoteServerError,
    ScopeNotFoundError,
    TemplateRenderingError,
)


class TestMapToHttpException:
    """Tests for map_to_http_exception method."""

    def test_scope_not_found_error_returns_404(self) -> None:
        """ScopeNotFoundError should map to 404."""
        error = ScopeNotFoundError("test-scope")
        result = ErrorMapper.map_to_http_exception(error, context="test-scope")
        assert isinstance(result, HTTPException)
        assert result.status_code == 404
        assert "test-scope" in result.detail

    def test_template_rendering_error_returns_422_with_generic_message(self) -> None:
        """TemplateRenderingError should map to 422 with generic message."""
        error = TemplateRenderingError("{{ undefined_var }}", "undefined_var")
        result = ErrorMapper.map_to_http_exception(error, context="test-scope")
        assert isinstance(result, HTTPException)
        assert result.status_code == 422
        assert result.detail == "Template rendering failed"
        assert "undefined_var" not in result.detail

    def test_daimyo_error_returns_500_with_generic_message(self) -> None:
        """DaimyoError should map to 500 with generic message."""
        error = InvalidScopeError("Invalid scope data")
        result = ErrorMapper.map_to_http_exception(error, context="test-scope")
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert result.detail == "Internal error occurred"
        assert "Invalid scope data" not in result.detail

    def test_remote_server_error_returns_500_with_generic_message(self) -> None:
        """RemoteServerError should map to 500 with generic message."""
        error = RemoteServerError("Connection failed", url="https://example.com")
        result = ErrorMapper.map_to_http_exception(error, context="test-scope")
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert result.detail == "Internal error occurred"
        assert "Connection failed" not in result.detail
        assert "https://example.com" not in result.detail

    def test_unexpected_error_returns_500_with_generic_message(self) -> None:
        """Unexpected errors should map to 500 with generic message."""
        error = ValueError("Unexpected value error")
        result = ErrorMapper.map_to_http_exception(error, context="test-scope")
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert result.detail == "Internal server error"
        assert "Unexpected value error" not in result.detail

    def test_context_parameter_is_optional(self) -> None:
        """Context parameter should be optional."""
        error = ScopeNotFoundError("test-scope")
        result = ErrorMapper.map_to_http_exception(error)
        assert isinstance(result, HTTPException)
        assert result.status_code == 404


class TestMapToErrorString:
    """Tests for map_to_error_string method."""

    def test_scope_not_found_error_returns_safe_message(self) -> None:
        """ScopeNotFoundError should return safe error string."""
        error = ScopeNotFoundError("test-scope", available_scopes=["scope1", "scope2"])
        result = ErrorMapper.map_to_error_string(error, context="test-scope")
        assert "Scope Error:" in result
        assert "test-scope" in result

    def test_template_rendering_error_returns_generic_message(self) -> None:
        """TemplateRenderingError should return generic message."""
        error = TemplateRenderingError("{{ undefined_var }}", "undefined_var")
        result = ErrorMapper.map_to_error_string(error, context="test-scope")
        assert result == "Template Error: Template rendering failed"
        assert "undefined_var" not in result
        assert "{{ undefined_var }}" not in result

    def test_daimyo_error_returns_generic_message(self) -> None:
        """DaimyoError should return generic message."""
        error = InvalidScopeError("Invalid scope data with sensitive info")
        result = ErrorMapper.map_to_error_string(error, context="test-scope")
        assert result == "Daimyo Error: Internal error occurred"
        assert "sensitive info" not in result

    def test_unexpected_error_returns_generic_message(self) -> None:
        """Unexpected errors should return generic message."""
        error = RuntimeError("Unexpected runtime error")
        result = ErrorMapper.map_to_error_string(error, context="test-scope")
        assert result == "Error: An unexpected error occurred"
        assert "Unexpected runtime error" not in result

    def test_context_parameter_is_optional(self) -> None:
        """Context parameter should be optional."""
        error = ScopeNotFoundError("test-scope")
        result = ErrorMapper.map_to_error_string(error)
        assert "Scope Error:" in result


class TestErrorDisclosurePrevention:
    """Tests ensuring no sensitive information is disclosed."""

    @pytest.mark.parametrize(
        "error",
        [
            TemplateRenderingError("{{ user_password }}", "user_password"),
            InvalidScopeError("/home/user/config.yaml: Invalid format"),
            RemoteServerError(
                "Failed to connect to https://internal-server.local:8080/api/v1/scopes"
            ),
            RuntimeError("/var/lib/app/data.db: Permission denied"),
        ],
    )
    def test_http_exception_never_discloses_sensitive_info(self, error: Exception) -> None:
        """HTTP exceptions should never contain file paths or sensitive data."""
        result = ErrorMapper.map_to_http_exception(error, context="test")
        assert "/home/" not in result.detail
        assert "/var/" not in result.detail
        assert "password" not in result.detail.lower()
        assert "internal-server" not in result.detail

    @pytest.mark.parametrize(
        "error",
        [
            TemplateRenderingError("{{ api_key }}", "api_key"),
            InvalidScopeError("Database connection string: postgresql://user:pass@localhost"),
            RemoteServerError("Token expired: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
            RuntimeError("Secret key: sk_live_abc123"),
        ],
    )
    def test_error_string_never_discloses_sensitive_info(self, error: Exception) -> None:
        """Error strings should never contain credentials or sensitive data."""
        result = ErrorMapper.map_to_error_string(error, context="test")
        assert "api_key" not in result
        assert "password" not in result.lower()
        assert "postgresql://" not in result
        assert "eyJ" not in result
        assert "sk_live" not in result


class TestConsistentErrorMessages:
    """Tests ensuring consistent error message format."""

    def test_all_http_exceptions_have_consistent_format(self) -> None:
        """All HTTP exceptions should have consistent detail format."""
        errors = [
            TemplateRenderingError("template", "var"),
            InvalidScopeError("error"),
            RemoteServerError("error"),
            RuntimeError("error"),
        ]

        for error in errors:
            result = ErrorMapper.map_to_http_exception(error, context="test")
            assert isinstance(result.detail, str)
            assert len(result.detail) > 0
            assert len(result.detail) < 100

    def test_all_error_strings_have_consistent_format(self) -> None:
        """All error strings should have consistent format."""
        errors = [
            ScopeNotFoundError("test"),
            TemplateRenderingError("template", "var"),
            InvalidScopeError("error"),
            RuntimeError("error"),
        ]

        for error in errors:
            result = ErrorMapper.map_to_error_string(error, context="test")
            assert ":" in result
            assert len(result) > 0
            assert len(result) < 100

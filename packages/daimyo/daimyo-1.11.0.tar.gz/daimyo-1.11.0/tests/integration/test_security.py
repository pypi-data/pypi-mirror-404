"""Security integration tests for injection prevention and safe error handling."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from daimyo.presentation.rest.app import app


class TestLogInjectionPrevention:
    """Tests for log injection attack prevention."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_scope_name_with_special_chars_rejected(self, client: TestClient) -> None:
        """Scope names with special characters should be rejected."""
        malicious_names = [
            "test@malicious",
            "test#malicious",
            "test$malicious",
            "test!malicious",
            "test malicious",
        ]
        for name in malicious_names:
            response = client.get(
                f"/api/v1/scopes/{name}/index",
                headers={"Accept": "application/json"},
            )
            assert response.status_code in (400, 404)

    def test_categories_with_newlines_rejected(self, client: TestClient) -> None:
        """Categories with newlines should be rejected."""
        response = client.get(
            "/api/v1/scopes/kencho/rules",
            params={"categories": "valid.category\nmalicious.injection"},
        )
        assert response.status_code == 400
        assert "Invalid category format" in response.json()["detail"]

    def test_categories_with_special_chars_rejected(self, client: TestClient) -> None:
        """Categories with special characters should be rejected."""
        malicious_categories = [
            "valid.category; DROP TABLE",
            "category@malicious",
            "category/path",
            "category\\path",
        ]
        for categories in malicious_categories:
            response = client.get(
                "/api/v1/scopes/kencho/rules",
                params={"categories": categories},
            )
            assert response.status_code == 400


class TestPathTraversalPrevention:
    """Tests for path traversal attack prevention."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_path_traversal_in_scope_name_rejected(self, client: TestClient) -> None:
        """Path traversal attempts in scope names should be rejected."""
        malicious_paths = [
            "../../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "test/../../../etc/passwd",
        ]
        for path in malicious_paths:
            response = client.get(f"/api/v1/scopes/{path}/index")
            assert response.status_code in (400, 404)


class TestSQLInjectionPrevention:
    """Tests for SQL injection attack prevention."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_sql_injection_in_scope_name_rejected(self, client: TestClient) -> None:
        """SQL injection attempts in scope names should be rejected."""
        sql_injections = [
            "test' OR '1'='1",
            "test'; DROP TABLE scopes; --",
            "test' UNION SELECT * FROM users--",
        ]
        for injection in sql_injections:
            response = client.get(f"/api/v1/scopes/{injection}/index")
            assert response.status_code == 400

    def test_sql_injection_in_categories_rejected(self, client: TestClient) -> None:
        """SQL injection attempts in categories should be rejected."""
        sql_injections = [
            "category'; DROP TABLE rules; --",
            "category' OR '1'='1",
        ]
        for injection in sql_injections:
            response = client.get(
                "/api/v1/scopes/kencho/rules",
                params={"categories": injection},
            )
            assert response.status_code == 400


class TestErrorDisclosure:
    """Tests for error information disclosure prevention."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_scope_not_found_error_is_safe(self, client: TestClient) -> None:
        """Scope not found errors should not expose internal details."""
        response = client.get(
            "/api/v1/scopes/nonexistent-scope-12345/index",
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "/home/" not in detail.lower()
        assert "traceback" not in detail.lower()
        assert ".py" not in detail.lower()
        assert "exception" not in detail.lower()

    def test_internal_errors_are_generic(self, client: TestClient) -> None:
        """Internal errors should return generic messages."""
        response = client.get("/api/v1/scopes/kencho/rules")
        if response.status_code == 500:
            detail = response.json()["detail"]
            assert detail in [
                "Internal server error",
                "Internal error occurred",
                "Template rendering failed",
            ]
            assert "/home/" not in detail.lower()
            assert "file" not in detail.lower()
            assert "traceback" not in detail.lower()


class TestInputValidation:
    """Tests for input validation edge cases."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_empty_scope_name_rejected(self, client: TestClient) -> None:
        """Empty scope names should be rejected."""
        response = client.get("/api/v1/scopes//index")
        assert response.status_code in (400, 404, 422)

    def test_very_long_scope_name_rejected(self, client: TestClient) -> None:
        """Scope names exceeding max length should be rejected."""
        long_name = "a" * 201
        response = client.get(f"/api/v1/scopes/{long_name}/index")
        assert response.status_code == 400
        assert "too long" in response.json()["detail"]

    def test_very_long_categories_rejected(self, client: TestClient) -> None:
        """Categories exceeding max length should be rejected."""
        long_categories = "a" * 10001
        response = client.get(
            "/api/v1/scopes/kencho/rules",
            params={"categories": long_categories},
        )
        assert response.status_code == 400
        assert "too long" in response.json()["detail"]

    def test_valid_scope_name_accepted(self, client: TestClient) -> None:
        """Valid scope names should be accepted."""
        valid_names = [
            "kencho",
            "python-general",
            "team_backend",
            "MixedCase123",
        ]
        for name in valid_names:
            response = client.get(
                f"/api/v1/scopes/{name}/index",
                headers={"Accept": "application/json"},
            )
            assert response.status_code in (200, 404)

    def test_valid_categories_accepted(self, client: TestClient) -> None:
        """Valid categories should be accepted."""
        valid_categories = [
            "development.coding.python",
            "general,security",
            "parent.child.grandchild",
        ]
        for categories in valid_categories:
            response = client.get(
                "/api/v1/scopes/kencho/rules",
                params={"categories": categories},
                headers={"Accept": "application/json"},
            )
            assert response.status_code in (200, 404)


class TestHeaderInjection:
    """Tests for header-based injection attacks."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_accept_header_with_newlines_handled(self, client: TestClient) -> None:
        """Accept headers with newlines should be handled safely."""
        response = client.get(
            "/api/v1/scopes/kencho/index",
            headers={"Accept": "application/json\nmalicious: header"},
        )
        assert response.status_code in (200, 404, 406)

    def test_accept_header_with_control_chars_handled(self, client: TestClient) -> None:
        """Accept headers with control characters should be handled safely."""
        response = client.get(
            "/api/v1/scopes/kencho/index",
            headers={"Accept": "application/json\r\nmalicious: value"},
        )
        assert response.status_code in (200, 404, 406)


class TestBoundaryValues:
    """Tests for boundary value validation."""

    @pytest.fixture()
    def client(self) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_scope_name_at_max_length_accepted(self, client: TestClient) -> None:
        """Scope name at exactly max length should be accepted."""
        max_length_name = "a" * 200
        response = client.get(
            f"/api/v1/scopes/{max_length_name}/index",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in (200, 404)

    def test_categories_at_max_length_accepted(self, client: TestClient) -> None:
        """Categories at exactly max length should be accepted."""
        max_length_categories = "a" * 10000
        response = client.get(
            "/api/v1/scopes/kencho/rules",
            params={"categories": max_length_categories},
            headers={"Accept": "application/json"},
        )
        assert response.status_code in (200, 404)

    def test_single_char_scope_name_accepted(self, client: TestClient) -> None:
        """Single character scope names should be accepted."""
        response = client.get(
            "/api/v1/scopes/a/index",
            headers={"Accept": "application/json"},
        )
        assert response.status_code in (200, 404)

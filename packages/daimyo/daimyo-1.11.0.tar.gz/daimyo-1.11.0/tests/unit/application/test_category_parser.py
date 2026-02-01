"""Tests for CategoryStringParser."""


from daimyo.application.filtering import CategoryStringParser


class TestCategoryStringParser:
    """Tests for category string parser."""

    def test_parse_simple_categories(self):
        """Test parsing simple comma-separated categories."""
        result = CategoryStringParser.parse("python.web,python.testing")
        assert result == ["python.web", "python.testing"]

    def test_parse_with_whitespace(self):
        """Test parsing categories with extra whitespace."""
        result = CategoryStringParser.parse("  python.web  , python.testing  ")
        assert result == ["python.web", "python.testing"]

    def test_parse_single_category(self):
        """Test parsing a single category."""
        result = CategoryStringParser.parse("python")
        assert result == ["python"]

    def test_parse_none(self):
        """Test parsing None returns empty list."""
        result = CategoryStringParser.parse(None)
        assert result == []

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty list."""
        result = CategoryStringParser.parse("")
        assert result == []

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns empty list."""
        result = CategoryStringParser.parse("   ")
        assert result == []

    def test_parse_complex_hierarchy(self):
        """Test parsing complex hierarchical categories."""
        result = CategoryStringParser.parse("python.web.api,python.testing.unit,javascript")
        assert result == ["python.web.api", "python.testing.unit", "javascript"]

    def test_parse_with_empty_elements(self):
        """Test parsing with empty elements (double commas)."""
        result = CategoryStringParser.parse("python.web,,python.testing")
        assert result == ["python.web", "python.testing"]

    def test_parse_trailing_comma(self):
        """Test parsing with trailing comma."""
        result = CategoryStringParser.parse("python.web,python.testing,")
        assert result == ["python.web", "python.testing"]

    def test_parse_leading_comma(self):
        """Test parsing with leading comma."""
        result = CategoryStringParser.parse(",python.web,python.testing")
        assert result == ["python.web", "python.testing"]


__all__ = ["TestCategoryStringParser"]

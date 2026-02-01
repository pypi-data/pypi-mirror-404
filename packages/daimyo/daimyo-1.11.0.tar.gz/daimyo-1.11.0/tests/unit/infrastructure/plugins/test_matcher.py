"""Tests for wildcard pattern matching."""

import pytest

from daimyo.infrastructure.plugins import WildcardMatcher


class TestWildcardMatcher:
    """Test wildcard pattern matching."""

    def test_exact_match(self):
        """Exact plugin name match."""
        matcher = WildcardMatcher(["git.branch"])
        assert matcher.matches("git.branch")
        assert not matcher.matches("git.commit")

    def test_wildcard_match(self):
        """Wildcard pattern matching."""
        matcher = WildcardMatcher(["git.*"])
        assert matcher.matches("git.branch")
        assert matcher.matches("git.commit")
        assert not matcher.matches("env.user")

    def test_nested_wildcard(self):
        """Nested wildcard patterns."""
        matcher = WildcardMatcher(["git.context.*"])
        assert matcher.matches("git.context.branch")
        assert matcher.matches("git.context.commit")
        assert not matcher.matches("git.branch")

    def test_multiple_patterns(self):
        """Multiple patterns combined."""
        matcher = WildcardMatcher(["git.*", "env.*"])
        assert matcher.matches("git.branch")
        assert matcher.matches("env.user")
        assert not matcher.matches("other.plugin")

    def test_star_wildcard_rejected(self):
        """Star pattern is not allowed."""
        from daimyo.domain import PluginConfigurationError

        with pytest.raises(PluginConfigurationError) as exc_info:
            WildcardMatcher(["*"])

        assert "not allowed" in str(exc_info.value).lower()

    def test_filter_plugins(self):
        """Filter plugin names by patterns."""
        matcher = WildcardMatcher(["git.*"])
        plugins = ["git.branch", "git.commit", "env.user", "git.remote"]
        filtered = matcher.filter_plugins(plugins)

        assert len(filtered) == 3
        assert "git.branch" in filtered
        assert "git.commit" in filtered
        assert "git.remote" in filtered
        assert "env.user" not in filtered

    def test_filter_with_multiple_patterns(self):
        """Filter with multiple patterns."""
        matcher = WildcardMatcher(["git.*", "env.user"])
        plugins = ["git.branch", "env.user", "env.hostname", "other.plugin"]
        filtered = matcher.filter_plugins(plugins)

        assert len(filtered) == 2
        assert "git.branch" in filtered
        assert "env.user" in filtered

    def test_no_match(self):
        """No pattern matches."""
        matcher = WildcardMatcher(["git.*"])
        assert not matcher.matches("env.user")
        assert not matcher.matches("completely.different")

    def test_empty_patterns(self):
        """Empty pattern list matches nothing."""
        matcher = WildcardMatcher([])
        assert not matcher.matches("anything")
        assert not matcher.matches("git.branch")

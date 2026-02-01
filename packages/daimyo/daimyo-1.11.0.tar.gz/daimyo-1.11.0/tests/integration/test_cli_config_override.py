"""Integration tests for CLI configuration override."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from daimyo.__main__ import app

runner = CliRunner()


@pytest.fixture
def custom_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with custom config and rules.

    :param tmp_path: Pytest tmp_path fixture
    :return: Path to custom directory
    """
    config_dir = tmp_path / "custom_config"
    config_dir.mkdir()

    config_file = config_dir / "settings.toml"
    config_file.write_text(
        """
[default]
RULES_PATH = "custom_rules"
LOG_LEVEL = "DEBUG"
"""
    )

    secrets_file = config_dir / ".secrets.toml"
    secrets_file.write_text("")

    rules_dir = tmp_path / "custom_rules"
    rules_dir.mkdir()

    test_scope_dir = rules_dir / "test-scope"
    test_scope_dir.mkdir()

    metadata_file = test_scope_dir / "metadata.yml"
    metadata_file.write_text(
        """name: test-scope
description: Test scope for integration tests
"""
    )

    scope_file = test_scope_dir / "scope.toml"
    scope_file.write_text(
        """
[commandments]
[suggestions]
"""
    )

    return tmp_path


class TestConfigOverride:
    """Tests for --config CLI flag."""

    def test_config_flag_with_list_scopes(self, custom_config_dir: Path) -> None:
        """CLI should use custom config when --config flag is provided."""
        config_path = custom_config_dir / "custom_config" / "settings.toml"
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "--rules-path",
                str(rules_path),
                "list-scopes",
            ],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout

    def test_short_config_flag(self, custom_config_dir: Path) -> None:
        """CLI should support -c short flag for config."""
        config_path = custom_config_dir / "custom_config" / "settings.toml"
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            [
                "-c",
                str(config_path),
                "--rules-path",
                str(rules_path),
                "list-scopes",
            ],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout


class TestRulesPathOverride:
    """Tests for --rules-path CLI flag."""

    def test_rules_path_flag_with_list_scopes(self, custom_config_dir: Path) -> None:
        """CLI should use custom rules path when --rules-path flag is provided."""
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            ["--rules-path", str(rules_path), "list-scopes"],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout

    def test_short_rules_path_flag(self, custom_config_dir: Path) -> None:
        """CLI should support -r short flag for rules path."""
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            ["-r", str(rules_path), "list-scopes"],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout

    def test_rules_path_with_show_command(self, custom_config_dir: Path) -> None:
        """CLI should use custom rules path with show command."""
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            ["--rules-path", str(rules_path), "show", "test-scope"],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout
        assert "Test scope for integration tests" in result.stdout


class TestBothOverrides:
    """Tests for using both --config and --rules-path together."""

    def test_both_flags_together(self, custom_config_dir: Path) -> None:
        """CLI should handle both --config and --rules-path flags together."""
        config_path = custom_config_dir / "custom_config" / "settings.toml"
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            [
                "--config",
                str(config_path),
                "--rules-path",
                str(rules_path),
                "list-scopes",
            ],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout

    def test_short_flags_together(self, custom_config_dir: Path) -> None:
        """CLI should handle both short flags together."""
        config_path = custom_config_dir / "custom_config" / "settings.toml"
        rules_path = custom_config_dir / "custom_rules"

        result = runner.invoke(
            app,
            [
                "-c",
                str(config_path),
                "-r",
                str(rules_path),
                "show",
                "test-scope",
            ],
        )

        assert result.exit_code == 0
        assert "test-scope" in result.stdout


class TestDefaultBehavior:
    """Tests that default behavior still works without override flags."""

    def test_list_scopes_without_flags(self) -> None:
        """CLI should work without any override flags."""
        result = runner.invoke(app, ["list-scopes"])

        assert result.exit_code == 0

    def test_version_flag(self) -> None:
        """Version flag should work independently of config override."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "daimyo version" in result.stdout

"""Tests for configuration discovery module."""

import os
from pathlib import Path
from unittest.mock import patch

from daimyo.config.discovery import (
    discover_config_file,
    discover_rules_path,
    discover_secrets_file,
)


class TestDiscoverConfigFile:
    """Tests for discover_config_file function."""

    def test_cli_config_takes_precedence(self) -> None:
        """CLI config argument should take precedence over everything."""
        cli_config = "/custom/path/config.toml"
        result = discover_config_file(cli_config)
        assert result == cli_config

    @patch.dict(os.environ, {"DAIMYO_CONFIG_FILE": "/env/config.toml"})
    def test_env_var_when_no_cli_arg(self) -> None:
        """Environment variable should be used when no CLI arg provided."""
        result = discover_config_file()
        assert result == "/env/config.toml"

    @patch.dict(os.environ, {"DAIMYO_CONFIG_FILE": "/env/config.toml"})
    def test_cli_arg_overrides_env_var(self) -> None:
        """CLI argument should override environment variable."""
        cli_config = "/custom/path/config.toml"
        result = discover_config_file(cli_config)
        assert result == cli_config

    @patch.dict(os.environ, {}, clear=True)
    def test_local_config_when_exists(self, tmp_path: Path) -> None:
        """Local config should be found when it exists."""
        local_config = tmp_path / ".daimyo" / "config" / "settings.toml"
        local_config.parent.mkdir(parents=True)
        local_config.touch()

        candidates = [
            tmp_path / ".daimyo" / "config" / "settings.toml",
            Path("/nonexistent") / ".daimyo" / "config" / "settings.toml",
            Path("/etc/daimyo/config/settings.toml"),
        ]

        def exists_side_effect(self: Path) -> bool:
            return self == candidates[0]

        with (
            patch.object(Path, "exists", exists_side_effect),
            patch.object(Path, "home", return_value=Path("/nonexistent")),
        ):
            result = discover_config_file()
            assert ".daimyo/config/settings.toml" in result

    def test_default_when_none_exist(self) -> None:
        """Default should be returned when no config files exist."""
        with patch.object(Path, "exists", return_value=False):
            result = discover_config_file()
            assert result == ".daimyo/config/settings.toml"


class TestDiscoverSecretsFile:
    """Tests for discover_secrets_file function."""

    def test_secrets_file_next_to_config(self) -> None:
        """Secrets file should be sibling of config file."""
        config_file = "/path/to/config/settings.toml"
        result = discover_secrets_file(config_file)
        assert result == "/path/to/config/.secrets.toml"

    def test_secrets_file_with_relative_path(self) -> None:
        """Secrets file should work with relative config path."""
        config_file = ".daimyo/config/settings.toml"
        result = discover_secrets_file(config_file)
        assert result == ".daimyo/config/.secrets.toml"


class TestDiscoverRulesPath:
    """Tests for discover_rules_path function."""

    def test_cli_rules_path_takes_precedence(self) -> None:
        """CLI rules path argument should take precedence over everything."""
        cli_rules = "/custom/rules"
        config_rules = "/config/rules"
        result = discover_rules_path(cli_rules, config_rules)
        assert result == cli_rules

    @patch.dict(os.environ, {"DAIMYO_RULES_PATH": "/env/rules"})
    def test_env_var_when_no_cli_arg(self) -> None:
        """Environment variable should be used when no CLI arg provided."""
        result = discover_rules_path()
        assert result == "/env/rules"

    @patch.dict(os.environ, {"DAIMYO_RULES_PATH": "/env/rules"})
    def test_cli_arg_overrides_env_var(self) -> None:
        """CLI argument should override environment variable."""
        cli_rules = "/custom/rules"
        result = discover_rules_path(cli_rules)
        assert result == cli_rules

    @patch.dict(os.environ, {}, clear=True)
    def test_config_rules_path_used_when_provided(self) -> None:
        """Config RULES_PATH should be used when provided."""
        config_rules = "/config/rules"
        result = discover_rules_path(config_rules_path=config_rules)
        assert result == config_rules

    def test_local_rules_when_exists(self, tmp_path: Path) -> None:
        """Local rules directory should be found when it exists."""
        local_rules = tmp_path / ".daimyo" / "rules"
        local_rules.mkdir(parents=True)

        candidates = [
            tmp_path / ".daimyo" / "rules",
            Path("/nonexistent") / ".daimyo" / "rules",
            Path("/etc/daimyo/rules"),
        ]

        def exists_side_effect(self: Path) -> bool:
            return self == candidates[0]

        def is_dir_side_effect(self: Path) -> bool:
            return self == candidates[0]

        with (
            patch.object(Path, "exists", exists_side_effect),
            patch.object(Path, "is_dir", is_dir_side_effect),
            patch.object(Path, "home", return_value=Path("/nonexistent")),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = discover_rules_path()
            assert ".daimyo/rules" in result

    @patch.dict(os.environ, {}, clear=True)
    def test_default_when_none_exist(self) -> None:
        """Default should be returned when no rules directories exist."""
        with (
            patch.object(Path, "exists", return_value=False),
            patch.object(Path, "is_dir", return_value=False),
        ):
            result = discover_rules_path()
            assert result == ".daimyo/rules"

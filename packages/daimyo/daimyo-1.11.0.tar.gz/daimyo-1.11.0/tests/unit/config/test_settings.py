"""Tests for settings module."""

from pathlib import Path

from daimyo.config.settings import SettingsProxy, get_settings, initialize_settings


class TestInitializeSettings:
    """Tests for initialize_settings function."""

    def test_initialize_with_custom_paths(self, tmp_path: Path) -> None:
        """Settings should be initialized with custom config and secrets paths."""
        config_file = tmp_path / "custom_config.toml"
        secrets_file = tmp_path / "custom_secrets.toml"

        config_file.write_text('[default]\nRULES_PATH = "/custom/rules"\n')
        secrets_file.write_text("")

        settings = initialize_settings(str(config_file), str(secrets_file))

        assert settings is not None
        assert settings.RULES_PATH == "/custom/rules"

    def test_reinitialize_with_different_paths(self, tmp_path: Path) -> None:
        """Settings can be reinitialized with different paths."""
        config1 = tmp_path / "config1.toml"
        config2 = tmp_path / "config2.toml"
        secrets = tmp_path / ".secrets.toml"

        config1.write_text('[default]\nRULES_PATH = "/rules1"\n')
        config2.write_text('[default]\nRULES_PATH = "/rules2"\n')
        secrets.write_text("")

        settings1 = initialize_settings(str(config1), str(secrets))
        assert settings1.RULES_PATH == "/rules1"

        settings2 = initialize_settings(str(config2), str(secrets))
        assert settings2.RULES_PATH == "/rules2"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_initializes_if_needed(self) -> None:
        """get_settings should initialize settings if not already done."""
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, "RULES_PATH")

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings should return the same instance on subsequent calls."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSettingsProxy:
    """Tests for SettingsProxy class."""

    def test_proxy_getattr(self) -> None:
        """SettingsProxy should delegate attribute access to settings."""
        proxy = SettingsProxy()
        assert hasattr(proxy, "RULES_PATH")
        assert isinstance(proxy.RULES_PATH, str)

    def test_proxy_setattr(self) -> None:
        """SettingsProxy should delegate attribute setting to settings."""
        proxy = SettingsProxy()
        original_value = proxy.RULES_PATH
        proxy.RULES_PATH = "/test/path"
        assert proxy.RULES_PATH == "/test/path"
        proxy.RULES_PATH = original_value

    def test_proxy_getitem(self) -> None:
        """SettingsProxy should support item access."""
        proxy = SettingsProxy()
        assert proxy["RULES_PATH"] is not None

    def test_proxy_setitem(self) -> None:
        """SettingsProxy should support item assignment."""
        proxy = SettingsProxy()
        original_value = proxy["RULES_PATH"]
        proxy["RULES_PATH"] = "/test/path"
        assert proxy["RULES_PATH"] == "/test/path"
        proxy["RULES_PATH"] = original_value

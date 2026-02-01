"""Configuration management using dynaconf."""

from typing import Any

from dynaconf import Dynaconf, Validator  # type: ignore[import-untyped]

_settings: Dynaconf | None = None


def _get_validators() -> list[Validator]:
    """Get list of configuration validators.

    :return: List of Dynaconf validators
    """
    return [
        Validator("RULES_PATH", default=".daimyo/rules"),
        Validator("LOG_LEVEL", default="INFO"),
        Validator("CONSOLE_LOG_LEVEL", default="INFO"),
        Validator("FILE_LOG_LEVEL", default="INFO"),
        Validator("LOG_FILE", default="logs/daimyo.log"),
        Validator("LOG_JSON_FILE", default="logs/daimyo.jsonl"),
        Validator("MAX_INHERITANCE_DEPTH", default=10, gte=1, lte=100),
        Validator("MASTER_SERVER_URL", default=""),
        Validator("REMOTE_TIMEOUT_SECONDS", default=5, gte=1, lte=60),
        Validator("REMOTE_MAX_RETRIES", default=3, gte=0, lte=10),
        Validator("REST_HOST", default="0.0.0.0"),
        Validator("REST_PORT", default=8000, gte=1, lte=65535),
        Validator("MCP_TRANSPORT", default="stdio", is_in=["stdio", "http"]),
        Validator("MCP_HOST", default="0.0.0.0"),
        Validator("MCP_PORT", default=8001, gte=1, lte=65535),
        Validator("ENABLED_PLUGINS", default=[]),
        Validator("RULES_MARKDOWN_PROLOGUE", default=""),
        Validator("RULES_MARKDOWN_EPILOGUE", default=""),
        Validator("INDEX_MARKDOWN_PROLOGUE", default=""),
        Validator("INDEX_MARKDOWN_EPILOGUE", default=""),
        Validator("DEFAULT_CATEGORY_DESCRIPTION", default="These rules apply at all times"),
        Validator("COMMANDMENTS_XML_TAG", default=""),
        Validator("SUGGESTIONS_XML_TAG", default=""),
        Validator("RULES_CATEGORIZED", default=True, is_type_of=bool),
        Validator("DEFAULT_SCOPE", default=""),
    ]


def initialize_settings(
    config_file: str = ".daimyo/config/settings.toml",
    secrets_file: str = ".daimyo/config/.secrets.toml",
) -> Dynaconf:
    """Initialize or reinitialize Dynaconf settings with custom paths.

    :param config_file: Path to configuration file
    :param secrets_file: Path to secrets file
    :return: Initialized Dynaconf instance
    """
    global _settings
    _settings = Dynaconf(
        envvar_prefix="DAIMYO",
        settings_files=[config_file, secrets_file],
        environments=True,
        load_dotenv=True,
        validators=_get_validators(),
    )
    return _settings


def get_settings() -> Dynaconf:
    """Get the settings instance, initializing if necessary.

    :return: Dynaconf settings instance
    """
    global _settings
    if _settings is None:
        _settings = initialize_settings()
    return _settings


class SettingsProxy:
    """Proxy for settings to maintain backward compatibility.

    Delegates all attribute access to the underlying Dynaconf instance.
    """

    def __getattr__(self, name: str) -> Any:
        """Get attribute from settings instance.

        :param name: Attribute name
        :return: Attribute value from settings
        """
        return getattr(get_settings(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute on settings instance.

        :param name: Attribute name
        :param value: Value to set
        """
        setattr(get_settings(), name, value)

    def __getitem__(self, key: str) -> Any:
        """Get item from settings instance.

        :param key: Setting key
        :return: Setting value
        """
        return get_settings()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item on settings instance.

        :param key: Setting key
        :param value: Value to set
        """
        get_settings()[key] = value


settings = SettingsProxy()

__all__ = ["settings", "initialize_settings", "get_settings"]

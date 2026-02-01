"""Configuration and rules path discovery.

This module provides functions to discover configuration files and rules directories
using a precedence hierarchy that supports multiple deployment scenarios.
"""

import os
from pathlib import Path


def discover_config_file(cli_config: str | None = None) -> str:
    """Discover configuration file using precedence order.

    Precedence (first found wins):
    1. CLI argument (--config)
    2. DAIMYO_CONFIG_FILE environment variable
    3. .daimyo/config/settings.toml (local project)
    4. ~/.daimyo/config/settings.toml (user home)
    5. /etc/daimyo/config/settings.toml (system-wide)
    6. Default: .daimyo/config/settings.toml

    :param cli_config: Optional config path from CLI --config flag
    :return: Path to configuration file (may not exist)
    """
    if cli_config:
        return cli_config

    env_config = os.environ.get("DAIMYO_CONFIG_FILE")
    if env_config:
        return env_config

    candidates = [
        Path(".daimyo/config/settings.toml"),
        Path.home() / ".daimyo/config/settings.toml",
        Path("/etc/daimyo/config/settings.toml"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return ".daimyo/config/settings.toml"


def discover_secrets_file(config_file: str) -> str:
    """Discover secrets file next to the configuration file.

    :param config_file: Path to the configuration file
    :return: Path to secrets file (sibling of config file)
    """
    config_path = Path(config_file)
    secrets_path = config_path.parent / ".secrets.toml"
    return str(secrets_path)


def discover_rules_path(
    cli_rules_path: str | None = None,
    config_rules_path: str | None = None,
) -> str:
    """Discover rules directory using precedence order.

    Precedence (first found wins):
    1. CLI argument (--rules-path)
    2. DAIMYO_RULES_PATH environment variable
    3. RULES_PATH from config file
    4. .daimyo/rules (local project, if exists)
    5. ~/.daimyo/rules (user home, if exists)
    6. /etc/daimyo/rules (system-wide, if exists)
    7. Default: .daimyo/rules

    :param cli_rules_path: Optional rules path from CLI --rules-path flag
    :param config_rules_path: Optional RULES_PATH from config file
    :return: Path to rules directory (may not exist)
    """
    if cli_rules_path:
        return cli_rules_path

    env_rules_path = os.environ.get("DAIMYO_RULES_PATH")
    if env_rules_path:
        return env_rules_path

    if config_rules_path:
        return config_rules_path

    candidates = [
        Path(".daimyo/rules"),
        Path.home() / ".daimyo/rules",
        Path("/etc/daimyo/rules"),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return str(candidate)

    return ".daimyo/rules"

"""Configuration management for Wizzlethorpe client."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "wizzlethorpe"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load configuration from file.

    Returns:
        dict: Configuration dictionary, empty dict if file doesn't exist or is invalid.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    # Set file permissions to user read/write only (0600)
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        # On Windows, chmod may not work as expected, but that's okay
        pass


def get_config_value(key: str) -> str | None:
    """Get a single configuration value.

    Args:
        key: Configuration key to retrieve.

    Returns:
        str | None: Configuration value, or None if key doesn't exist.
    """
    return load_config().get(key)


def set_config_value(key: str, value: str) -> None:
    """Set a single configuration value.

    Args:
        key: Configuration key to set.
        value: Configuration value to set.
    """
    config = load_config()
    config[key] = value
    save_config(config)


def unset_config_value(key: str) -> None:
    """Remove a configuration value.

    Args:
        key: Configuration key to remove.
    """
    config = load_config()
    if key in config:
        del config[key]
        save_config(config)


def list_config() -> dict:
    """List all configuration values.

    Returns:
        dict: All configuration values.
    """
    return load_config()

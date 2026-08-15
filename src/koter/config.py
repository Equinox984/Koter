"""Koter configuration using standard TOML."""

import os
import tomllib
from pathlib import Path
from typing import Any


# Default paths
DEFAULT_VAULT = Path.home() / "Koter"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "koter"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_default_config() -> dict:
    """Returns default configuration."""
    return {
        "vault": str(DEFAULT_VAULT),
        "editor": "",  # Empty = use $EDITOR
        "theme": "mono",
        "history": {
            "keep": 100  # 0 = no limit
        }
    }


def load_config() -> dict:
    """Loads configuration from TOML file."""
    config = get_default_config()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                file_config = tomllib.load(f)
                # Merge with defaults
                for key, value in file_config.items():
                    if isinstance(value, dict) and key in config:
                        config[key].update(value)
                    else:
                        config[key] = value
        except (tomllib.TOMLDecodeError, IOError):
            pass
    
    # Environment variable can override vault
    env_vault = os.environ.get("KOTER_VAULT")
    if env_vault:
        config["vault"] = env_vault
    
    return config


def save_config(config: dict) -> None:
    """Saves configuration to TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build TOML manually (no external write libraries)
    lines = []
    
    # Simple keys first
    simple_keys = ["vault", "editor", "theme"]
    for key in simple_keys:
        if key in config:
            value = config[key]
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f"{key} = {value}")
    
    # History section
    if "history" in config and isinstance(config["history"], dict):
        lines.append("")
        lines.append("[history]")
        for k, v in config["history"].items():
            lines.append(f"{k} = {v}")
    
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_config_value(key: str, subkey: str = None) -> Any:
    """Gets a specific value from configuration."""
    config = load_config()
    
    if subkey:
        return config.get(key, {}).get(subkey)
    return config.get(key)


def set_config_value(key: str, value: Any, subkey: str = None) -> None:
    """Sets a value in configuration and saves."""
    config = load_config()
    
    if subkey:
        if key not in config:
            config[key] = {}
        config[key][subkey] = value
    else:
        config[key] = value
    
    save_config(config)


def ensure_vault_exists() -> Path:
    """Ensures vault exists and returns its path."""
    config = load_config()
    vault = Path(config["vault"])
    vault.mkdir(parents=True, exist_ok=True)
    return vault

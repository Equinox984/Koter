"""Configuración de Koter usando TOML estándar."""

import os
import tomllib
from pathlib import Path
from typing import Any


# Rutas por defecto
DEFAULT_VAULT = Path.home() / "Koter"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "koter"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_default_config() -> dict:
    """Devuelve la configuración por defecto."""
    return {
        "vault": str(DEFAULT_VAULT),
        "editor": "",  # Vacío = usar $EDITOR
        "theme": "mono",
        "history": {
            "keep": 100  # 0 = sin límite
        }
    }


def load_config() -> dict:
    """Carga la configuración desde el archivo TOML."""
    config = get_default_config()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as f:
                file_config = tomllib.load(f)
                # Fusionar con defaults
                for key, value in file_config.items():
                    if isinstance(value, dict) and key in config:
                        config[key].update(value)
                    else:
                        config[key] = value
        except (tomllib.TOMLDecodeError, IOError):
            pass
    
    # Variable de entorno puede sobrescribir vault
    env_vault = os.environ.get("KOTER_VAULT")
    if env_vault:
        config["vault"] = env_vault
    
    return config


def save_config(config: dict) -> None:
    """Guarda la configuración al archivo TOML."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Construir TOML manualmente (sin librerías externas de escritura)
    lines = []
    
    # Claves simples primero
    simple_keys = ["vault", "editor", "theme"]
    for key in simple_keys:
        if key in config:
            value = config[key]
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f"{key} = {value}")
    
    # Sección history
    if "history" in config and isinstance(config["history"], dict):
        lines.append("")
        lines.append("[history]")
        for k, v in config["history"].items():
            lines.append(f"{k} = {v}")
    
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_config_value(key: str, subkey: str = None) -> Any:
    """Obtiene un valor específico de la configuración."""
    config = load_config()
    
    if subkey:
        return config.get(key, {}).get(subkey)
    return config.get(key)


def set_config_value(key: str, value: Any, subkey: str = None) -> None:
    """Establece un valor en la configuración y guarda."""
    config = load_config()
    
    if subkey:
        if key not in config:
            config[key] = {}
        config[key][subkey] = value
    else:
        config[key] = value
    
    save_config(config)


def ensure_vault_exists() -> Path:
    """Asegura que el vault existe y devuelve su ruta."""
    config = load_config()
    vault = Path(config["vault"])
    vault.mkdir(parents=True, exist_ok=True)
    return vault

"""Gestión de temas para Koter."""

import tomllib
from pathlib import Path
from typing import Optional

from .config import CONFIG_DIR


# Tokens de estilo disponibles
STYLE_TOKENS = ["accent", "dim", "header", "selected", "error"]

# Tema mono por defecto (solo atributos, sin colores)
DEFAULT_THEMES = {
    "mono": {
        "accent": {"attr": "bold"},
        "dim": {"attr": "dim"},
        "header": {"attr": "bold"},
        "selected": {"attr": "reverse"},
        "error": {"attr": "bold"},
    }
}


def get_themes_dir() -> Path:
    """Devuelve el directorio de temas."""
    themes_dir = CONFIG_DIR / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    return themes_dir


def load_theme(name: str) -> dict:
    """Carga un tema por nombre."""
    # Verificar temas por defecto
    if name in DEFAULT_THEMES:
        return DEFAULT_THEMES[name]
    
    # Buscar en archivo
    themes_dir = get_themes_dir()
    theme_file = themes_dir / f"{name}.toml"
    
    if not theme_file.exists():
        return DEFAULT_THEMES["mono"]
    
    try:
        with open(theme_file, "rb") as f:
            return tomllib.load(f)
    except (tomllib.TOMLDecodeError, IOError):
        return DEFAULT_THEMES["mono"]


def get_active_theme(theme_name: str = None) -> dict:
    """Obtiene el tema activo desde configuración o parámetro."""
    if theme_name is None:
        from .config import get_config_value
        theme_name = get_config_value("theme") or "mono"
    
    return load_theme(theme_name)


def list_themes() -> list[str]:
    """Lista todos los temas disponibles."""
    themes = list(DEFAULT_THEMES.keys())
    
    themes_dir = get_themes_dir()
    if themes_dir.exists():
        for f in themes_dir.glob("*.toml"):
            themes.append(f.stem)
    
    return themes


def save_theme(name: str, theme_data: dict) -> None:
    """Guarda un tema personalizado."""
    themes_dir = get_themes_dir()
    theme_file = themes_dir / f"{name}.toml"
    
    # Construir TOML manualmente
    lines = [f"# Tema: {name}", ""]
    
    for token, attrs in theme_data.items():
        lines.append(f"[{token}]")
        for attr, value in attrs.items():
            if isinstance(value, str):
                lines.append(f'{attr} = "{value}"')
            else:
                lines.append(f"{attr} = {value}")
        lines.append("")
    
    theme_file.write_text("\n".join(lines))

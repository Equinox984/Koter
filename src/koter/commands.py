"""Registro de comandos y handlers para Koter."""

import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from .models import Result, Note
from .storage import (
    create_note, list_notes, get_note, update_note,
    move_to_trash, restore_from_trash
)
from .config import load_config, get_config_value, set_config_value, save_config


@dataclass
class Command:
    """Definición de un comando."""
    name: str
    handler: Callable
    help_text: str
    aliases: list[str] = None
    args: list[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.args is None:
            self.args = []


# Registro de comandos
COMMANDS: dict[str, Command] = {}


def register_command(name: str, help_text: str, aliases: list[str] = None, args: list[str] = None):
    """Decorador para registrar un comando."""
    def decorator(func: Callable) -> Callable:
        cmd = Command(name=name, handler=func, help_text=help_text, aliases=aliases or [], args=args or [])
        COMMANDS[name] = cmd
        for alias in cmd.aliases:
            COMMANDS[alias] = cmd
        return func
    return decorator


def open_editor(path: str) -> None:
    """Abre el editor configurado para un archivo."""
    config = load_config()
    editor = config.get("editor") or os.environ.get("EDITOR") or "vim"
    
    # Ejecutar editor
    subprocess.run([editor, path])


@register_command(
    "new",
    "Crear una nueva nota",
    args=["title", "--tags"]
)
def cmd_new(title: str, tags: str = None) -> Result:
    """Crea una nueva nota y abre el editor."""
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
    
    note = create_note(title, tag_list)
    open_editor(note.path)
    
    # Recargar después de editar
    note = get_note(note.slug)
    return Result.message(f"Nota '{note.title}' creada en {note.path}")


@register_command(
    "capture",
    "Crear nota con contenido desde stdin",
    args=["title"]
)
def cmd_capture(title: str) -> Result:
    """Crea una nota con contenido leído desde stdin."""
    import sys
    content = sys.stdin.read()
    
    note = create_note(title, [])
    update_note(note.slug, content.strip())
    
    return Result.message(f"Nota '{note.title}' capturada")


@register_command(
    "list",
    "Listar notas",
    aliases=["ls"],
    args=["--tag", "--pinned"]
)
def cmd_list(tag: str = None, pinned: bool = False) -> Result:
    """Lista todas las notas visibles."""
    notes = list_notes(tag=tag, pinned_only=pinned)
    return Result.notes(notes)


@register_command(
    "edit",
    "Editar una nota existente",
    aliases=["e"],
    args=["slug"]
)
def cmd_edit(slug: str) -> Result:
    """Abre una nota en el editor."""
    note = get_note(slug)
    if note is None:
        return Result.error(f"Nota '{slug}' no encontrada")
    
    open_editor(note.path)
    
    # Recargar después de editar
    note = get_note(slug)
    return Result.message(f"Nota '{note.title}' editada")


@register_command(
    "view",
    "Ver contenido de una nota",
    args=["slug"]
)
def cmd_view(slug: str) -> Result:
    """Muestra el contenido de una nota."""
    note = get_note(slug)
    if note is None:
        return Result.error(f"Nota '{slug}' no encontrada")
    
    return Result.text(note.content)


@register_command(
    "search",
    "Buscar texto en notas",
    aliases=["sr"],
    args=["query"]
)
def cmd_search(query: str) -> Result:
    """Busca texto en título y cuerpo de notas."""
    # Implementación básica para Fase 0 - se completará en Fase 2
    from .search import search_notes
    results = search_notes(query)
    return Result.notes(results) if results else Result.message("No se encontraron coincidencias")


@register_command(
    "rm",
    "Mover nota a papelera",
    aliases=["delete", "del"],
    args=["slug"]
)
def cmd_rm(slug: str) -> Result:
    """Mueve una nota a la papelera."""
    if move_to_trash(slug):
        return Result.message(f"Nota movida a papelera")
    return Result.error(f"Nota '{slug}' no encontrada")


@register_command(
    "restore",
    "Restaurar nota desde papelera",
    args=["slug"]
)
def cmd_restore(slug: str) -> Result:
    """Restaura una nota desde la papelera."""
    if restore_from_trash(slug):
        return Result.message(f"Nota restaurada")
    return Result.error(f"No se encontró '{slug}' en papelera")


@register_command(
    "history",
    "Ver historial de versiones",
    args=["slug"]
)
def cmd_history(slug: str) -> Result:
    """Lista snapshots de una nota."""
    # Para Fase 0 - se implementará en Fase 3
    return Result.message("Historial no implementado aún")


@register_command(
    "revert",
    "Revertir a versión anterior",
    args=["slug", "id"]
)
def cmd_revert(slug: str, id: str) -> Result:
    """Restaura una versión anterior."""
    # Para Fase 0 - se implementará en Fase 3
    return Result.message("Revert no implementado aún")


@register_command(
    "config",
    "Gestionar configuración",
    args=["action", "key", "value"]
)
def cmd_config(action: str, key: str = None, value: str = None) -> Result:
    """Muestra o modifica configuración."""
    config = load_config()
    
    if action == "show":
        # Formatear config para mostrar
        lines = []
        for k, v in config.items():
            if isinstance(v, dict):
                for sk, sv in v.items():
                    lines.append(f"{k}.{sk} = {sv}")
            else:
                lines.append(f"{k} = {v}")
        return Result.text("\n".join(lines))
    
    elif action == "get":
        if not key:
            return Result.error("Se requiere clave para 'get'")
        val = get_config_value(key)
        if val is not None:
            return Result.text(str(val))
        return Result.error(f"Clave '{key}' no encontrada")
    
    elif action == "set":
        if not key or value is None:
            return Result.error("Se requiere clave y valor para 'set'")
        set_config_value(key, value)
        return Result.message(f"Configuración actualizada: {key} = {value}")
    
    elif action == "edit":
        from .config import CONFIG_FILE
        if not CONFIG_FILE.exists():
            # Crear archivo vacío con defaults
            save_config(config)
        open_editor(str(CONFIG_FILE))
        return Result.message("Configuración editada")
    
    return Result.error(f"Acción desconocida: {action}")


@register_command(
    "tag",
    "Gestionar tags",
    args=["subcommand", "slug", "tag"]
)
def cmd_tag(subcommand: str, slug: str = None, tag: str = None) -> Result:
    """Gestiona tags de notas."""
    # Para Fase 1
    return Result.message("Comando tag no implementado aún")


@register_command(
    "pin",
    "Fijar nota",
    args=["slug"]
)
def cmd_pin(slug: str) -> Result:
    """Fija una nota."""
    # Para Fase 1
    return Result.message("Comando pin no implementado aún")


@register_command(
    "unpin",
    "Desfijar nota",
    args=["slug"]
)
def cmd_unpin(slug: str) -> Result:
    """Desfija una nota."""
    # Para Fase 1
    return Result.message("Comando unpin no implementado aún")


@register_command(
    "help",
    "Mostrar ayuda",
    aliases=["h", "?"]
)
def cmd_help(command: str = None) -> Result:
    """Muestra ayuda general o de un comando específico."""
    if command and command in COMMANDS:
        cmd = COMMANDS[command]
        lines = [
            f"Usage: {cmd.name}",
            f"  {cmd.help_text}",
        ]
        if cmd.args:
            lines.append(f"  Args: {', '.join(cmd.args)}")
        return Result.text("\n".join(lines))
    
    # Ayuda general
    lines = ["Comandos disponibles:", ""]
    seen = set()
    for name, cmd in sorted(COMMANDS.items()):
        if cmd.name in seen:
            continue
        seen.add(cmd.name)
        alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
        lines.append(f"  {cmd.name}{alias_str}: {cmd.help_text}")
    
    return Result.text("\n".join(lines))


def dispatch_command(name: str, args: dict) -> Result:
    """Ejecuta un comando con sus argumentos."""
    if name not in COMMANDS:
        return Result.error(f"Comando desconocido: {name}")
    
    cmd = COMMANDS[name]
    try:
        return cmd.handler(**args)
    except TypeError as e:
        return Result.error(f"Error en argumentos: {e}")
    except Exception as e:
        return Result.error(str(e))


def parse_cli_args(args: list[str]) -> tuple[str, dict]:
    """Parsea argumentos CLI simples."""
    if not args:
        return "help", {}
    
    cmd_name = args[0]
    remaining = args[1:]
    
    parsed = {}
    positional = []
    i = 0
    
    # Obtuir definición del comando para saber sus args esperados
    cmd = COMMANDS.get(cmd_name)
    expected_args = cmd.args if cmd else []
    
    while i < len(remaining):
        arg = remaining[i]
        
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(remaining) and not remaining[i + 1].startswith("--"):
                parsed[key] = remaining[i + 1]
                i += 2
            else:
                parsed[key] = True
                i += 1
        else:
            positional.append(arg)
            i += 1
    
    # Asignar posicionales según orden esperado
    if expected_args:
        for idx, arg_name in enumerate(expected_args):
            if not arg_name.startswith("--"):
                if idx < len(positional):
                    parsed[arg_name] = positional[idx]
    
    return cmd_name, parsed

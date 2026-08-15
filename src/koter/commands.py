"""Command registry and handlers for Koter."""

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
    """Command definition."""
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
    """Decorator to register a command."""
    def decorator(func: Callable) -> Callable:
        cmd = Command(name=name, handler=func, help_text=help_text, aliases=aliases or [], args=args or [])
        COMMANDS[name] = cmd
        for alias in cmd.aliases:
            COMMANDS[alias] = cmd
        return func
    return decorator


def open_editor(path: str) -> None:
    """Opens the configured editor for a file."""
    config = load_config()
    editor = config.get("editor") or os.environ.get("EDITOR") or "vim"
    
    # Run editor
    subprocess.run([editor, path])


@register_command(
    "new",
    "Create a new note",
    args=["title", "--tags"]
)
def cmd_new(title: str, tags: str = None) -> Result:
    """Creates a new note and opens the editor."""
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
    
    note = create_note(title, tag_list)
    open_editor(note.path)
    
    # Reload after editing
    note = get_note(note.slug)
    return Result.message(f"Note '{note.title}' created at {note.path}")


@register_command(
    "capture",
    "Create note with content from stdin",
    args=["title"]
)
def cmd_capture(title: str) -> Result:
    """Creates a note with content read from stdin."""
    import sys
    content = sys.stdin.read()
    
    note = create_note(title, [])
    update_note(note.slug, content.strip())
    
    return Result.message(f"Note '{note.title}' captured")


@register_command(
    "list",
    "List notes",
    aliases=["ls"],
    args=["--tag", "--pinned"]
)
def cmd_list(tag: str = None, pinned: bool = False) -> Result:
    """Lists all visible notes."""
    notes = list_notes(tag=tag, pinned_only=pinned)
    return Result.notes(notes)


@register_command(
    "edit",
    "Edit an existing note",
    aliases=["e"],
    args=["slug"]
)
def cmd_edit(slug: str) -> Result:
    """Opens a note in the editor."""
    note = get_note(slug)
    if note is None:
        return Result.error(f"Note '{slug}' not found")
    
    open_editor(note.path)
    
    # Reload after editing
    note = get_note(slug)
    return Result.message(f"Note '{note.title}' edited")


@register_command(
    "view",
    "View note content",
    args=["slug"]
)
def cmd_view(slug: str) -> Result:
    """Displays the content of a note."""
    note = get_note(slug)
    if note is None:
        return Result.error(f"Note '{slug}' not found")
    
    return Result.text(note.content)


@register_command(
    "search",
    "Search text in notes",
    aliases=["sr"],
    args=["query"]
)
def cmd_search(query: str) -> Result:
    """Searches text in title and body of notes."""
    # Basic implementation for Phase 0 - will be completed in Phase 2
    from .search import search_notes
    from .render import render_search_results
    results = search_notes(query)
    if not results:
        return Result.message("No matches found")
    lines = render_search_results(results)
    return Result.text("\n".join(lines))


@register_command(
    "rm",
    "Move note to trash",
    aliases=["delete", "del"],
    args=["slug"]
)
def cmd_rm(slug: str) -> Result:
    """Moves a note to the trash."""
    if move_to_trash(slug):
        return Result.message(f"Note moved to trash")
    return Result.error(f"Note '{slug}' not found")


@register_command(
    "restore",
    "Restore note from trash",
    args=["slug"]
)
def cmd_restore(slug: str) -> Result:
    """Restores a note from the trash."""
    if restore_from_trash(slug):
        return Result.message(f"Note restored")
    return Result.error(f"'{slug}' not found in trash")


@register_command(
    "history",
    "View version history",
    args=["slug"]
)
def cmd_history(slug: str) -> Result:
    """Lists snapshots of a note."""
    # Para Fase 0 - se implementará en Fase 3
    return Result.message("History not implemented yet")


@register_command(
    "revert",
    "Revert to previous version",
    args=["slug", "id"]
)
def cmd_revert(slug: str, id: str) -> Result:
    """Restores a previous version."""
    # Para Fase 0 - se implementará en Fase 3
    return Result.message("Revert not implemented yet")


@register_command(
    "config",
    "Manage configuration",
    args=["action", "key", "value"]
)
def cmd_config(action: str, key: str = None, value: str = None) -> Result:
    """Shows or modifies configuration."""
    config = load_config()
    
    if action == "show":
        # Format config for display
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
            return Result.error("Key required for 'get'")
        val = get_config_value(key)
        if val is not None:
            return Result.text(str(val))
        return Result.error(f"Key '{key}' not found")
    
    elif action == "set":
        if not key or value is None:
            return Result.error("Key and value required for 'set'")
        set_config_value(key, value)
        return Result.message(f"Configuration updated: {key} = {value}")
    
    elif action == "edit":
        from .config import CONFIG_FILE
        if not CONFIG_FILE.exists():
            # Create empty file with defaults
            save_config(config)
        open_editor(str(CONFIG_FILE))
        return Result.message("Configuration edited")
    
    return Result.error(f"Unknown action: {action}")


@register_command(
    "tag",
    "Manage tags",
    args=["subcommand", "slug", "tag"]
)
def cmd_tag(subcommand: str, slug: str = None, tag: str = None) -> Result:
    """Manages note tags."""
    # For Phase 1
    return Result.message("Tag command not implemented yet")


@register_command(
    "pin",
    "Pin note",
    args=["slug"]
)
def cmd_pin(slug: str) -> Result:
    """Pins a note."""
    # For Phase 1
    return Result.message("Pin command not implemented yet")


@register_command(
    "unpin",
    "Unpin note",
    args=["slug"]
)
def cmd_unpin(slug: str) -> Result:
    """Unpins a note."""
    # For Phase 1
    return Result.message("Unpin command not implemented yet")


@register_command(
    "help",
    "Show help",
    aliases=["h", "?"]
)
def cmd_help(command: str = None) -> Result:
    """Shows general help or help for a specific command."""
    if command and command in COMMANDS:
        cmd = COMMANDS[command]
        lines = [
            f"Usage: {cmd.name}",
            f"  {cmd.help_text}",
        ]
        if cmd.args:
            lines.append(f"  Args: {', '.join(cmd.args)}")
        return Result.text("\n".join(lines))
    
    # General help
    lines = ["Available commands:", ""]
    seen = set()
    for name, cmd in sorted(COMMANDS.items()):
        if cmd.name in seen:
            continue
        seen.add(cmd.name)
        alias_str = f" ({', '.join(cmd.aliases)})" if cmd.aliases else ""
        lines.append(f"  {cmd.name}{alias_str}: {cmd.help_text}")
    
    return Result.text("\n".join(lines))


def dispatch_command(name: str, args: dict) -> Result:
    """Executes a command with its arguments."""
    if name not in COMMANDS:
        return Result.error(f"Unknown command: {name}")
    
    cmd = COMMANDS[name]
    try:
        return cmd.handler(**args)
    except TypeError as e:
        return Result.error(f"Argument error: {e}")
    except Exception as e:
        return Result.error(str(e))


def parse_cli_args(args: list[str]) -> tuple[str, dict]:
    """Parses simple CLI arguments."""
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
    
    # Assign positionals according to expected order
    if expected_args:
        for idx, arg_name in enumerate(expected_args):
            if not arg_name.startswith("--"):
                if idx < len(positional):
                    parsed[arg_name] = positional[idx]
    
    return cmd_name, parsed

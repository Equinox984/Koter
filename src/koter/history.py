"""Historial de versiones por snapshots."""

from pathlib import Path
from datetime import datetime
import os

from .config import load_config
from .storage import get_vault_path, get_note, note_from_path


def get_history_path(slug: str) -> Path:
    """Devuelve la ruta del directorio de historial para una nota."""
    vault = get_vault_path()
    history_dir = vault / ".koter" / "history" / slug
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def save_snapshot(slug: str, content: str) -> str:
    """
    Guarda un snapshot del contenido actual.
    Devuelve el ID del snapshot (timestamp).
    """
    history_dir = get_history_path(slug)
    epoch = int(datetime.now().timestamp())
    snapshot_file = history_dir / f"{epoch}.md"
    snapshot_file.write_text(content)
    return str(epoch)


def list_snapshots(slug: str) -> list[dict]:
    """
    Lista todos los snapshots de una nota, más reciente primero.
    Devuelve lista de dicts con id (epoch) y modified (fecha legible).
    """
    history_dir = get_history_path(slug)
    
    if not history_dir.exists():
        return []
    
    snapshots = []
    for f in history_dir.glob("*.md"):
        try:
            epoch = int(f.stem)
            modified = datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
            snapshots.append({
                "id": str(epoch),
                "modified": modified,
                "path": str(f)
            })
        except (ValueError, OSError):
            continue
    
    # Ordenar por más reciente primero
    snapshots.sort(key=lambda s: s["id"], reverse=True)
    return snapshots


def get_snapshot(slug: str, snapshot_id: str) -> str:
    """Obtiene el contenido de un snapshot específico."""
    history_dir = get_history_path(slug)
    snapshot_file = history_dir / f"{snapshot_id}.md"
    
    if not snapshot_file.exists():
        return ""
    
    return snapshot_file.read_text()


def prune_history(slug: str, keep: int = None) -> None:
    """
    Elimina snapshots antiguos según la configuración keep.
    keep = 0 significa sin límite.
    """
    if keep is None:
        config = load_config()
        keep = config.get("history", {}).get("keep", 100)
    
    if keep == 0:
        return
    
    snapshots = list_snapshots(slug)
    
    # Eliminar excedentes
    for snapshot in snapshots[keep:]:
        try:
            Path(snapshot["path"]).unlink()
        except OSError:
            pass


def revert_to_snapshot(slug: str, snapshot_id: str) -> bool:
    """
    Revierte una nota a un snapshot específico.
    Antes de revertir, guarda snapshot de la versión actual.
    """
    note = get_note(slug)
    if note is None:
        return False
    
    # Leer contenido del snapshot
    snapshot_content = get_snapshot(slug, snapshot_id)
    if not snapshot_content:
        return False
    
    # Guardar snapshot de la versión actual antes de revertir
    from .frontmatter import parse_frontmatter
    current_full = Path(note.path).read_text()
    _, current_body = parse_frontmatter(current_full)
    save_snapshot(slug, current_body)
    
    # Escribir contenido del snapshot
    from .storage import update_note
    update_note(slug, snapshot_content)
    
    # Podar historial
    prune_history(slug)
    
    return True

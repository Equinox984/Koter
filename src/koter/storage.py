"""Almacenamiento y gestión de notas en el vault."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .frontmatter import parse_frontmatter, update_note_content, get_note_metadata
from .models import Note
from .config import load_config, ensure_vault_exists


# Directorios internos (invisibles para list/search)
TRASH_DIR = ".trash"
HISTORY_DIR_NAME = Path(".koter") / "history"


def get_vault_path() -> Path:
    """Devuelve la ruta del vault configurado."""
    return ensure_vault_exists()


def get_trash_path() -> Path:
    """Devuelve la ruta de la papelera."""
    vault = get_vault_path()
    trash = vault / TRASH_DIR
    trash.mkdir(parents=True, exist_ok=True)
    return trash


def get_history_path(slug: str) -> Path:
    """Devuelve la ruta del historial para una nota."""
    vault = get_vault_path()
    history = vault / HISTORY_DIR_NAME / slug
    history.mkdir(parents=True, exist_ok=True)
    return history


def slugify(title: str) -> str:
    """Convierte un título a slug válido para filename."""
    # Minúsculas
    slug = title.lower()
    # Espacios a guiones
    slug = slug.replace(" ", "-")
    # Eliminar caracteres raros (solo permitir alfanuméricos y guiones)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Eliminar guiones múltiples consecutivos
    slug = re.sub(r'-+', '-', slug)
    # Eliminar guiones al inicio/final
    slug = slug.strip('-')
    return slug or "nota"


def get_unique_slug(slug: str) -> str:
    """Genera un slug único si hay colisión."""
    vault = get_vault_path()
    
    if not (vault / f"{slug}.md").exists():
        return slug
    
    # Hay colisión, agregar sufijo numérico
    counter = 2
    while (vault / f"{slug}-{counter}.md").exists():
        counter += 1
    
    return f"{slug}-{counter}"


def note_from_path(path: Path) -> Optional[Note]:
    """Crea un objeto Note desde un archivo."""
    if not path.exists():
        return None
    
    content = path.read_text()
    metadata, body = parse_frontmatter(content)
    
    slug = path.stem
    
    return Note(
        slug=slug,
        title=metadata.get('title', slug),
        created=metadata.get('created', ''),
        modified=metadata.get('modified', ''),
        tags=metadata.get('tags', []),
        pinned=metadata.get('pinned', False),
        content=body,
        path=str(path)
    )


def list_notes(tag: str = None, pinned_only: bool = False) -> list[Note]:
    """
    Lista todas las notas visibles.
    - Excluye .trash/ y .koter/
    - Si tag especificado, filtra por tag
    - Si pinned_only, solo notas pinneadas
    - Orden: pinneds primero, luego modified desc
    """
    vault = get_vault_path()
    notes = []
    
    for path in vault.glob("*.md"):
        # Saltar directorios internos (no deberían coincidir con *.md pero por seguridad)
        if path.name.startswith('.'):
            continue
        
        note = note_from_path(path)
        if note is None:
            continue
        
        # Filtros
        if pinned_only and not note.pinned:
            continue
        
        if tag and tag not in note.tags:
            continue
        
        notes.append(note)
    
    # Ordenar: pinneds primero, luego modified desc
    notes.sort(key=lambda n: (not n.pinned, n.modified), reverse=False)
    # Invertir para modified desc dentro de cada grupo
    notes.sort(key=lambda n: n.modified, reverse=True)
    notes.sort(key=lambda n: not n.pinned)
    
    return notes


def create_note(title: str, tags: list[str] = None) -> Note:
    """Crea una nueva nota y devuelve el objeto Note."""
    tags = tags or []
    vault = get_vault_path()
    
    slug = slugify(title)
    unique_slug = get_unique_slug(slug)
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    path = vault / f"{unique_slug}.md"
    
    update_note_content(
        path=path,
        title=title,
        content="",
        tags=tags,
        pinned=False,
        created=now,
        modified=now
    )
    
    return note_from_path(path)


def get_note(slug: str) -> Optional[Note]:
    """Obtiene una nota por slug (soporta prefijo único)."""
    vault = get_vault_path()
    
    # Intento directo
    path = vault / f"{slug}.md"
    if path.exists():
        return note_from_path(path)
    
    # Buscar por prefijo único
    matches = [p for p in vault.glob("*.md") if p.stem.startswith(slug) and not p.name.startswith('.')]
    
    if len(matches) == 1:
        return note_from_path(matches[0])
    elif len(matches) > 1:
        # Múltiples coincidencias, ambiguo
        raise ValueError(f"Prefijo '{slug}' es ambiguo. Coincide con: {[p.stem for p in matches]}")
    
    return None


def update_note(slug: str, content: str) -> Note:
    """Actualiza el contenido de una nota."""
    note = get_note(slug)
    if note is None:
        raise ValueError(f"Nota '{slug}' no encontrada")
    
    path = Path(note.path)
    metadata = get_note_metadata(path)
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    update_note_content(
        path=path,
        title=metadata.get('title', note.title),
        content=content,
        tags=metadata.get('tags', []),
        pinned=metadata.get('pinned', False),
        created=metadata.get('created'),
        modified=now
    )
    
    return note_from_path(path)


def move_to_trash(slug: str) -> bool:
    """Mueve una nota a la papelera."""
    note = get_note(slug)
    if note is None:
        return False
    
    trash = get_trash_path()
    src = Path(note.path)
    dst = trash / src.name
    
    # Manejar colisión en trash
    counter = 2
    while dst.exists():
        dst = trash / f"{src.stem}-{counter}.md"
        counter += 1
    
    src.rename(dst)
    return True


def restore_from_trash(slug: str) -> bool:
    """Restaura una nota desde la papelera."""
    trash = get_trash_path()
    vault = get_vault_path()
    
    # Buscar en trash
    src = trash / f"{slug}.md"
    if not src.exists():
        # Intentar por prefijo
        matches = [p for p in trash.glob("*.md") if p.stem.startswith(slug)]
        if len(matches) == 1:
            src = matches[0]
        else:
            return False
    
    dst = vault / src.name
    
    # Manejar colisión en vault
    if dst.exists():
        counter = 2
        while (vault / f"{src.stem}-{counter}.md").exists():
            counter += 1
        dst = vault / f"{src.stem}-{counter}.md"
    
    src.rename(dst)
    return True

"""Tests para storage.py."""

import pytest
from pathlib import Path
import os
import tempfile

from koter.storage import (
    slugify, get_unique_slug, note_from_path, list_notes,
    create_note, get_note, move_to_trash, restore_from_trash
)
from koter.config import DEFAULT_VAULT


@pytest.fixture
def temp_vault(tmp_path, monkeypatch):
    """Fixture para crear un vault temporal."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    monkeypatch.setenv("KOTER_VAULT", str(vault))
    return vault


def test_slugify_basic():
    """Test slugificación básica."""
    assert slugify("Mi Nota") == "mi-nota"
    assert slugify("Hello World!") == "hello-world"
    assert slugify("Test 123") == "test-123"


def test_slugify_special_chars():
    """Test slugificación con caracteres especiales."""
    assert slugify("Nota con ñ") == "nota-con"
    assert slugify("Café & Té") == "caf-t"


def test_slugify_empty():
    """Test slugificación de string vacío."""
    assert slugify("") == "nota"


def test_get_unique_slug_no_collision(temp_vault):
    """Test slug único sin colisión."""
    # Vault vacío, no debería haber colisión
    assert get_unique_slug("test") == "test"


def test_get_unique_slug_with_collision(temp_vault):
    """Test slug único con colisión."""
    # Crear archivo que cause colisión
    (temp_vault / "test.md").touch()
    
    assert get_unique_slug("test") == "test-2"
    
    (temp_vault / "test-2.md").touch()
    assert get_unique_slug("test") == "test-3"


def test_create_note(temp_vault):
    """Test creación de nota."""
    note = create_note("Prueba", tags=["test"])
    
    assert note is not None
    assert note.title == "Prueba"
    assert "test" in note.tags
    assert note.slug == "prueba"
    
    # Verificar archivo existe
    note_file = temp_vault / f"{note.slug}.md"
    assert note_file.exists()


def test_list_notes_empty(temp_vault):
    """Test listar notas vacías."""
    notes = list_notes()
    assert notes == []


def test_list_notes_with_notes(temp_vault):
    """Test listar notas con contenido."""
    create_note("Nota 1")
    create_note("Nota 2")
    
    notes = list_notes()
    assert len(notes) == 2
    
    titles = [n.title for n in notes]
    assert "Nota 1" in titles
    assert "Nota 2" in titles


def test_get_note_by_slug(temp_vault):
    """Test obtener nota por slug."""
    note = create_note("Test Note")
    
    retrieved = get_note(note.slug)
    assert retrieved is not None
    assert retrieved.title == "Test Note"


def test_get_note_by_prefix(temp_vault):
    """Test obtener nota por prefijo único."""
    create_note("Nota Larga")
    
    # Debería encontrar por prefijo
    retrieved = get_note("nota-l")
    assert retrieved is not None
    assert retrieved.title == "Nota Larga"


def test_move_to_trash(temp_vault):
    """Test mover nota a papelera."""
    note = create_note("Para Borrar")
    
    trash_dir = temp_vault / ".trash"
    assert not trash_dir.exists() or len(list(trash_dir.glob("*.md"))) == 0
    
    result = move_to_trash(note.slug)
    assert result is True
    
    # Nota ya no está en vault principal
    assert not (temp_vault / f"{note.slug}.md").exists()
    
    # Nota está en trash
    assert (trash_dir / f"{note.slug}.md").exists()


def test_restore_from_trash(temp_vault):
    """Test restaurar nota desde papelera."""
    note = create_note("Para Restaurar")
    move_to_trash(note.slug)
    
    # Verificar que está en trash
    assert not (temp_vault / f"{note.slug}.md").exists()
    
    # Restaurar
    result = restore_from_trash(note.slug)
    assert result is True
    
    # Verificar que volvió al vault
    assert (temp_vault / f"{note.slug}.md").exists()

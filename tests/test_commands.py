"""Tests para commands.py."""

import pytest
from unittest.mock import patch, MagicMock
import os

from koter.commands import (
    COMMANDS, dispatch_command, cmd_new, cmd_list, cmd_edit,
    cmd_view, cmd_help
)
from koter.models import ResultKind


@pytest.fixture
def temp_vault(tmp_path, monkeypatch):
    """Fixture para crear un vault temporal."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    monkeypatch.setenv("KOTER_VAULT", str(vault))
    return vault


def test_commands_registered():
    """Test que los comandos están registrados."""
    assert "new" in COMMANDS
    assert "list" in COMMANDS
    assert "edit" in COMMANDS
    assert "help" in COMMANDS


def test_help_command():
    """Test comando help."""
    result = cmd_help()
    
    assert result.kind == ResultKind.TEXT
    assert "Comandos disponibles" in result.data


def test_help_specific_command():
    """Test ayuda para comando específico."""
    result = cmd_help("new")
    
    assert result.kind == ResultKind.TEXT
    assert "new" in result.data


def test_list_empty(temp_vault):
    """Test listar cuando no hay notas."""
    result = cmd_list()
    
    assert result.kind == ResultKind.NOTES
    assert result.data == []


def test_list_with_notes(temp_vault):
    """Test listar con notas existentes."""
    from koter.storage import create_note
    
    create_note("Nota 1")
    create_note("Nota 2")
    
    result = cmd_list()
    
    assert result.kind == ResultKind.NOTES
    assert len(result.data) == 2


def test_dispatch_unknown_command():
    """Test despachar comando desconocido."""
    result = dispatch_command("comando-inexistente", {})
    
    assert result.kind == ResultKind.ERROR
    assert "desconocido" in result.message.lower()


def test_view_nonexistent_note(temp_vault):
    """Test ver nota que no existe."""
    result = cmd_view("nota-inexistente")
    
    assert result.kind == ResultKind.ERROR
    assert "no encontrada" in result.message.lower()


def test_edit_nonexistent_note(temp_vault):
    """Test editar nota que no existe."""
    result = cmd_edit("nota-inexistente")
    
    assert result.kind == ResultKind.ERROR


@patch('koter.commands.open_editor')
def test_new_creates_note(mock_editor, temp_vault):
    """Test que new crea una nota."""
    # Mock para evitar abrir editor real
    mock_editor.return_value = None
    
    # Simular que get_note devuelve algo después de crear
    with patch('koter.commands.get_note') as mock_get:
        mock_get.return_value = MagicMock(
            title="Prueba",
            path=str(temp_vault / "prueba.md"),
            slug="prueba"
        )
        
        result = cmd_new("Prueba")
        
        assert result.kind == ResultKind.MESSAGE
        assert "Prueba" in result.message
        
        # Verificar que se intentó abrir el editor
        mock_editor.assert_called_once()

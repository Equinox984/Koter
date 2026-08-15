"""Tests para frontmatter.py."""

import pytest
from pathlib import Path
import tempfile
import os

from koter.frontmatter import parse_frontmatter, build_frontmatter, update_note_content, get_note_metadata


def test_parse_frontmatter_simple():
    """Test parsing de frontmatter básico."""
    content = """---
title: Mi Nota
created: 2024-01-01
modified: 2024-01-02
tags: [test, demo]
pinned: false
---

Contenido de la nota.
"""
    metadata, body = parse_frontmatter(content)
    
    assert metadata["title"] == "Mi Nota"
    assert metadata["created"] == "2024-01-01"
    assert metadata["modified"] == "2024-01-02"
    assert metadata["tags"] == ["test", "demo"]
    assert metadata["pinned"] is False
    assert body.strip() == "Contenido de la nota."


def test_parse_frontmatter_empty():
    """Test contenido sin frontmatter."""
    content = "Solo contenido, sin frontmatter."
    metadata, body = parse_frontmatter(content)
    
    assert metadata == {}
    assert body == content


def test_parse_frontmatter_multiline_tags():
    """Test tags en múltiples líneas."""
    content = """---
title: Test
tags:
  - tag1
  - tag2
  - tag3
---

Body here.
"""
    metadata, body = parse_frontmatter(content)
    
    assert metadata["title"] == "Test"
    assert metadata["tags"] == ["tag1", "tag2", "tag3"]
    assert body.strip() == "Body here."


def test_build_frontmatter_basic():
    """Test construcción de frontmatter."""
    metadata = {
        "title": "Test Note",
        "created": "2024-01-01",
        "modified": "2024-01-02",
        "tags": ["a", "b"],
        "pinned": True
    }
    
    result = build_frontmatter(metadata)
    
    assert result.startswith("---")
    assert "title: Test Note" in result
    assert "created: 2024-01-01" in result
    assert "tags:" in result
    assert "pinned: true" in result


def test_update_note_content_creates_file(tmp_path):
    """Test creación de nota con frontmatter."""
    note_path = tmp_path / "test.md"
    
    update_note_content(
        path=note_path,
        title="Nueva Nota",
        content="Contenido inicial",
        tags=["test"],
        pinned=False,
        created="2024-01-01",
        modified="2024-01-01"
    )
    
    assert note_path.exists()
    content = note_path.read_text()
    
    assert "title: Nueva Nota" in content
    assert "Contenido inicial" in content
    assert "tags:" in content


def test_get_note_metadata(tmp_path):
    """Test lectura de metadata."""
    note_path = tmp_path / "test.md"
    note_path.write_text("""---
title: Meta Test
created: 2024-01-01
tags: [meta, test]
---

Content.
""")
    
    metadata = get_note_metadata(note_path)
    
    assert metadata["title"] == "Meta Test"
    assert metadata["created"] == "2024-01-01"
    assert metadata["tags"] == ["meta", "test"]

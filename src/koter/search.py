"""Búsqueda de texto en notas."""

from pathlib import Path
from .models import SearchResult, Note
from .storage import get_vault_path, note_from_path


def search_notes(query: str) -> list[SearchResult]:
    """
    Busca texto case-insensitive en título y cuerpo de notas.
    Devuelve lista de SearchResult con archivo, línea y contexto.
    """
    vault = get_vault_path()
    results = []
    query_lower = query.lower()
    
    for path in vault.glob("*.md"):
        # Saltar archivos ocultos
        if path.name.startswith('.'):
            continue
        
        try:
            content = path.read_text()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    results.append(SearchResult(
                        file_path=str(path),
                        line_number=line_num,
                        line_content=line.strip(),
                        match_context=path.stem
                    ))
        except (IOError, UnicodeDecodeError):
            continue
    
    return results

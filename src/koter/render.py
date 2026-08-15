"""Renderizado de resultados a texto con tokens de estilo."""

from typing import Iterable
from .models import Result, ResultKind, Note, SearchResult


# Tokens de estilo para diferentes tipos de contenido
STYLE_TOKENS = {
    "header": "",      # Encabezados
    "accent": "",      # Elementos destacados
    "dim": "",         # Texto secundario
    "selected": "",    # Elemento seleccionado (TUI)
    "error": "",       # Errores
    "note_title": "",  # Título de nota
    "note_slug": "",   # Slug de nota
    "note_tags": "",   # Tags
    "note_date": "",   # Fechas
    "search_file": "", # Archivo en búsqueda
    "search_line": "", # Número de línea
}


def render_result(result: Result, use_styles: bool = False) -> list[str]:
    """
    Convierte un Result en líneas de texto.
    Si use_styles es True, agrega tokens de estilo.
    """
    lines = []
    
    if result.kind == ResultKind.ERROR:
        prefix = "[ERROR] " if use_styles else ""
        return [f"{prefix}{result.message}"]
    
    if result.kind == ResultKind.MESSAGE:
        return [result.message]
    
    if result.kind == ResultKind.TEXT:
        return result.data.split('\n') if result.data else []
    
    if result.kind == ResultKind.NOTES:
        notes = result.data or []
        if not notes:
            return ["No hay notas."]
        
        for note in notes:
            pin_indicator = "★ " if note.pinned else "  "
            title_line = f"{pin_indicator}{note.title}"
            
            meta_parts = []
            if note.modified:
                meta_parts.append(note.modified)
            if note.tags:
                meta_parts.append(f"tags: {', '.join(note.tags)}")
            
            meta_line = "  " + " | ".join(meta_parts) if meta_parts else ""
            
            lines.append(title_line)
            if meta_line:
                lines.append(meta_line)
    
    return lines


def render_search_results(results: list[SearchResult], use_styles: bool = False) -> list[str]:
    """Renderiza resultados de búsqueda."""
    lines = []
    
    for res in results:
        file_part = res.file_path.split('/')[-1]
        line_str = f"{file_part}:{res.line_number}"
        lines.append(f"{line_str}: {res.line_content}")
    
    return lines


def format_note_list(notes: list[Note], use_styles: bool = False) -> list[str]:
    """Formatea una lista de notas para mostrar."""
    lines = []
    
    for note in notes:
        pin = "★ " if note.pinned else "  "
        title = f"{pin}{note.title}"
        
        parts = []
        if note.modified:
            parts.append(note.modified)
        if note.tags:
            parts.append(f"[{','.join(note.tags)}]")
        
        meta = "  " + "  ".join(parts) if parts else ""
        
        lines.append(title)
        if meta:
            lines.append(meta)
    
    return lines

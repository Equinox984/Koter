"""Modelos de datos para Koter."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ResultKind(Enum):
    """Tipos de resultado que pueden devolver los handlers."""
    NOTES = "notes"       # Lista de notas para renderizar
    TEXT = "text"         # Texto plano (ej: config show)
    MESSAGE = "message"   # Mensaje informativo
    ERROR = "error"       # Error


@dataclass
class Note:
    """Representa una nota con su metadata."""
    slug: str
    title: str
    created: str
    modified: str
    tags: list[str]
    pinned: bool
    content: str  # Contenido sin frontmatter
    path: str     # Ruta completa al archivo
    
    def __post_init__(self):
        if not isinstance(self.tags, list):
            self.tags = []


@dataclass
class SearchResult:
    """Resultado de una búsqueda."""
    file_path: str
    line_number: int
    line_content: str
    match_context: str


@dataclass
class Result:
    """Resultado uniforme de un comando."""
    kind: ResultKind
    data: any = None
    message: str = ""
    
    @classmethod
    def notes(cls, notes: list[Note]) -> "Result":
        return cls(kind=ResultKind.NOTES, data=notes)
    
    @classmethod
    def text(cls, text: str) -> "Result":
        return cls(kind=ResultKind.TEXT, data=text)
    
    @classmethod
    def message(cls, msg: str) -> "Result":
        return cls(kind=ResultKind.MESSAGE, message=msg)
    
    @classmethod
    def error(cls, msg: str) -> "Result":
        return cls(kind=ResultKind.ERROR, message=msg)

"""Data models for Koter."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ResultKind(Enum):
    """Result types that handlers can return."""
    NOTES = "notes"       # List of notes to render
    TEXT = "text"         # Plain text (e.g., config show)
    MESSAGE = "message"   # Informative message
    ERROR = "error"       # Error


@dataclass
class Note:
    """Represents a note with its metadata."""
    slug: str
    title: str
    created: str
    modified: str
    tags: list[str]
    pinned: bool
    content: str  # Content without frontmatter
    path: str     # Full file path
    
    def __post_init__(self):
        if not isinstance(self.tags, list):
            self.tags = []


@dataclass
class SearchResult:
    """Search result."""
    file_path: str
    line_number: int
    line_content: str
    match_context: str


@dataclass
class Result:
    """Uniform result from a command."""
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

"""Pick a loader by file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from . import docx, markdown, pdf, txt
from .base import (
    EmptyDocument,
    LoaderError,
    TextBlock,
    UnsupportedFileType,
    clean_text,
)

Loader = Callable[[Path], list[TextBlock]]

LOADERS: dict[str, Loader] = {
    ".txt": txt.load,
    ".text": txt.load,
    ".log": txt.load,
    ".md": markdown.load,
    ".markdown": markdown.load,
    ".pdf": pdf.load,
    ".docx": docx.load,
}

SUPPORTED_SUFFIXES = tuple(sorted(LOADERS))


def load_document(path: str | Path) -> list[TextBlock]:
    """Load any supported file into text blocks."""
    target = Path(path)
    if not target.exists():
        raise LoaderError(f"File not found: {target}")
    if not target.is_file():
        raise LoaderError(f"Not a file: {target}")

    loader = LOADERS.get(target.suffix.lower())
    if loader is None:
        raise UnsupportedFileType(
            f"Unsupported file type '{target.suffix}'. "
            f"Supported: {', '.join(SUPPORTED_SUFFIXES)}."
        )

    blocks = [block for block in loader(target) if block.text.strip()]
    if not blocks:
        raise EmptyDocument(f"{target.name} contains no text.")
    return blocks


__all__ = [
    "EmptyDocument",
    "LoaderError",
    "SUPPORTED_SUFFIXES",
    "TextBlock",
    "UnsupportedFileType",
    "clean_text",
    "load_document",
]

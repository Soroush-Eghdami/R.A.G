"""Plain text files."""

from __future__ import annotations

from pathlib import Path

from .base import LoaderError, TextBlock, blocks_from_plain_text

ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def read_text(path: Path) -> str:
    """Read a text file, falling back through common encodings."""
    raw = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise LoaderError(f"Could not decode {path.name}.")


def load(path: Path) -> list[TextBlock]:
    try:
        text = read_text(path)
    except OSError as exc:
        raise LoaderError(f"Could not read {path.name}: {exc}") from exc
    return blocks_from_plain_text(text)

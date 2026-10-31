"""Shared loader types."""

from __future__ import annotations

import re
from dataclasses import dataclass


class LoaderError(Exception):
    """Could not read a document."""


class UnsupportedFileType(LoaderError):
    """No loader for this extension."""


class EmptyDocument(LoaderError):
    """File loaded but has no text."""


@dataclass(frozen=True, slots=True)
class TextBlock:
    """A piece of text plus where it came from."""

    text: str
    page: int | None = None
    heading: str | None = None


def clean_text(text: str) -> str:
    """Tidy whitespace, keep paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def blocks_from_plain_text(text: str) -> list[TextBlock]:
    """Wrap plain text in a single block; the chunker handles the rest."""
    cleaned = clean_text(text)
    return [TextBlock(cleaned)] if cleaned else []

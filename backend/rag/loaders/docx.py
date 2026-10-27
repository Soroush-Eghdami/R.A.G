"""DOCX files.

Walks paragraphs and tables in order and tracks Word headings.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from .base import EmptyDocument, LoaderError, TextBlock, clean_text

HEADING_PREFIX = "heading"


def _heading_level(paragraph: Paragraph) -> int | None:
    style = (paragraph.style.name or "") if paragraph.style is not None else ""
    lowered = style.lower()
    if not lowered.startswith(HEADING_PREFIX):
        return None
    _, _, suffix = lowered.partition(" ")
    try:
        return max(1, int(suffix.strip()))
    except ValueError:
        return 1


def _table_text(table: Table) -> str:
    rows: list[str] = []
    for row in table.rows:
        cells = [clean_text(cell.text).replace("\n", " ") for cell in row.cells]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def load(path: Path) -> list[TextBlock]:
    try:
        document = Document(str(path))
    except Exception as exc:  # noqa: BLE001 - python-docx raises many types
        raise LoaderError(f"Could not open {path.name}: {exc}") from exc

    blocks: list[TextBlock] = []
    heading_stack: list[tuple[int, str]] = []

    def current_heading() -> str | None:
        if not heading_stack:
            return None
        return " > ".join(title for _, title in heading_stack)

    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(child, document)
            text = clean_text(paragraph.text)
            level = _heading_level(paragraph)
            if level is not None:
                heading_stack = [(d, t) for d, t in heading_stack if d < level]
                if text:
                    heading_stack.append((level, text))
                continue
            if text:
                blocks.append(TextBlock(text=text, heading=current_heading()))
        elif tag == "tbl":
            text = clean_text(_table_text(Table(child, document)))
            if text:
                blocks.append(TextBlock(text=text, heading=current_heading()))

    if not blocks:
        raise EmptyDocument(f"{path.name} contains no text.")
    return blocks

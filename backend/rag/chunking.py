"""Split text into overlapping chunks on natural breaks.

900 chars / 120 overlap by default: v1's 500/50 shredded context and made the
retriever fetch more chunks for the same answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .loaders import TextBlock, clean_text

BREAK_CHARS = frozenset(".!?;\n")


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    chunk_size: int = 900
    chunk_overlap: int = 120
    min_chunk_chars: int = 60

    def __post_init__(self) -> None:
        if self.chunk_size < 100:
            raise ValueError("chunk_size must be at least 100 characters")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.min_chunk_chars < 0:
            raise ValueError("min_chunk_chars cannot be negative")


@dataclass(frozen=True, slots=True)
class Chunk:
    """One embeddable unit of text."""

    text: str
    index: int
    page: int | None = None
    heading: str | None = None


def _find_break(text: str, start: int, end: int) -> int:
    """Cut at a sentence end if there is one in the back half of the window."""
    floor = start + max(1, (end - start) // 2)
    for position in range(end - 1, floor - 1, -1):
        if text[position] in BREAK_CHARS:
            return position + 1
    return end


def split_text(text: str, config: ChunkConfig | None = None) -> list[str]:
    """Split raw text into overlapping windows."""
    config = config or ChunkConfig()
    text = clean_text(text)
    if not text:
        return []
    if len(text) <= config.chunk_size:
        return [text]

    pieces: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + config.chunk_size, length)
        if end < length:
            end = _find_break(text, start, end)
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= length:
            break
        next_start = end - config.chunk_overlap
        start = next_start if next_start > start else start + 1

    # Fold a tiny tail into the previous chunk.
    if len(pieces) > 1 and len(pieces[-1]) < config.min_chunk_chars:
        tail = pieces.pop()
        pieces[-1] = f"{pieces[-1]} {tail}".strip()
    return pieces


def chunk_blocks(
    blocks: Iterable[TextBlock],
    config: ChunkConfig | None = None,
) -> list[Chunk]:
    """Chunk blocks, keeping page and heading info."""
    config = config or ChunkConfig()
    chunks: list[Chunk] = []
    for block in blocks:
        prefix = f"[Section: {block.heading}]\n" if block.heading else ""
        for piece in split_text(block.text, config):
            text = f"{prefix}{piece}" if prefix and not piece.startswith(prefix) else piece
            chunks.append(
                Chunk(
                    text=text,
                    index=len(chunks),
                    page=block.page,
                    heading=block.heading,
                )
            )
    return chunks


def chunk_text(text: str, config: ChunkConfig | None = None) -> list[Chunk]:
    """Chunk a plain string."""
    config = config or ChunkConfig()
    return [
        Chunk(text=piece, index=index)
        for index, piece in enumerate(split_text(text, config))
    ]

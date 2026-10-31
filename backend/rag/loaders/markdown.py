"""Markdown files.

Keeps the heading trail so chunks know which section they belong to.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import LoaderError, TextBlock, clean_text
from .txt import read_text

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
INLINE_RE = re.compile(r"(\*\*|__|`|~~)")


def _strip_inline(line: str) -> str:
    """Drop markdown noise the model does not need."""
    line = LINK_RE.sub(r"\1", line)
    line = INLINE_RE.sub("", line)
    return re.sub(r"^\s*(?:[-*+]\s+|\d+\.\s+|>\s*)", "", line)


def load(path: Path) -> list[TextBlock]:
    try:
        raw = read_text(path)
    except OSError as exc:
        raise LoaderError(f"Could not read {path.name}: {exc}") from exc

    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Skip YAML front matter.
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                lines = lines[index + 1 :]
                break

    blocks: list[TextBlock] = []
    heading_stack: list[tuple[int, str]] = []
    paragraph: list[str] = []
    in_fence = False

    def current_heading() -> str | None:
        if not heading_stack:
            return None
        return " > ".join(title for _, title in heading_stack)

    def flush() -> None:
        if not paragraph:
            return
        text = clean_text("\n".join(paragraph))
        paragraph.clear()
        if text:
            blocks.append(TextBlock(text=text, heading=current_heading()))

    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            flush()
            continue
        if not in_fence:
            match = HEADING_RE.match(line)
            if match:
                flush()
                level = len(match.group(1))
                title = match.group(2).strip()
                heading_stack = [(d, t) for d, t in heading_stack if d < level]
                if title:
                    heading_stack.append((level, title))
                continue
            if not line.strip():
                flush()
                continue
        paragraph.append(line if in_fence else _strip_inline(line))

    flush()
    return blocks

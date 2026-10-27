"""Prompt text and context formatting."""

from __future__ import annotations

from typing import Any, Sequence

from .vectorstore import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using ONLY the context below.\n"
    "If the context does not contain the answer, say you don't know. Do not invent facts.\n"
    "Cite the sources you use like [1], [2] matching the numbered context blocks."
)

NO_ANSWER = "I couldn't find that in your documents."


def source_label(chunk: RetrievedChunk) -> str:
    """Human readable source, e.g. ``report.pdf, p.4``."""
    name = chunk.document_name or chunk.document_id or "source"
    if chunk.page is not None:
        return f"{name}, p.{chunk.page}"
    return name


def build_context(chunks: Sequence[RetrievedChunk]) -> str:
    """Numbered context blocks, in the same order as the citations."""
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        blocks.append(f"[{number}] ({source_label(chunk)})\n{chunk.text}")
    return "\n\n".join(blocks)


def build_messages(
    question: str,
    chunks: Sequence[RetrievedChunk],
    history: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """System prompt with context, recent history, then the question."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{build_context(chunks)}"}
    ]
    for message in history:
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": str(content)})
    messages.append({"role": "user", "content": question})
    return messages

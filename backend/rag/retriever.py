"""Pick the chunks worth putting in front of the model."""

from __future__ import annotations

from dataclasses import dataclass

from .embedder import Embedder
from .vectorstore import RetrievedChunk, VectorStore


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    top_k: int = 4
    # Keep this threshold loose; the prompt handles off-topic matches.
    max_distance: float | None = 0.65


def retrieve(
    store: VectorStore,
    embedder: Embedder,
    kb_id: str,
    question: str,
    config: RetrievalConfig | None = None,
) -> list[RetrievedChunk]:
    """Return the closest chunks that pass the distance threshold."""
    config = config or RetrievalConfig()
    question = question.strip()
    if not question:
        return []

    embedding = embedder.embed_query(question)
    chunks = store.query(kb_id, embedding, top_k=config.top_k)
    if config.max_distance is None:
        return chunks
    return [chunk for chunk in chunks if chunk.distance <= config.max_distance]

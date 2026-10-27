"""Embed text with Ollama, applying each model's task prefixes."""

from __future__ import annotations

from typing import Protocol, Sequence

from .ollama_client import OllamaClient, OllamaResponseError

# model name fragment -> (document prefix, query prefix)
PREFIXES: dict[str, tuple[str, str]] = {
    "nomic-embed-text": ("search_document: ", "search_query: "),
    "nomic": ("search_document: ", "search_query: "),
    "e5-": ("passage: ", "query: "),
    "mxbai-embed": ("", "Represent this sentence for searching relevant passages: "),
}

DEFAULT_BATCH_SIZE = 32


def prefixes_for(model: str) -> tuple[str, str]:
    """Return (document prefix, query prefix) for a model."""
    base = model.split(":", 1)[0].strip().lower()
    for fragment, prefixes in PREFIXES.items():
        if fragment in base:
            return prefixes
    return ("", "")


class Embedder(Protocol):
    """Anything that turns text into vectors."""

    model: str

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class OllamaEmbedder:
    """Batch embedder over POST /api/embed."""

    def __init__(
        self,
        client: OllamaClient,
        model: str,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        document_prefix: str | None = None,
        query_prefix: str | None = None,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        default_doc, default_query = prefixes_for(model)
        self.client = client
        self.model = model
        self.batch_size = batch_size
        self.document_prefix = default_doc if document_prefix is None else document_prefix
        self.query_prefix = default_query if query_prefix is None else query_prefix

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(items), self.batch_size):
            batch = [
                self.document_prefix + text
                for text in items[start : start + self.batch_size]
            ]
            embedded = self.client.embed(self.model, batch)
            if len(embedded) != len(batch):
                raise OllamaResponseError(
                    f"Embedding model '{self.model}' returned {len(embedded)} "
                    f"vectors for {len(batch)} inputs."
                )
            vectors.extend(embedded)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        embedded = self.client.embed(self.model, [self.query_prefix + text])
        if not embedded:
            raise OllamaResponseError(
                f"Embedding model '{self.model}' returned no vector for the question."
            )
        return embedded[0]

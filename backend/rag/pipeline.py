"""Ingest documents and answer questions. No Django in here."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Literal, Sequence
from uuid import uuid4

from .chunking import ChunkConfig, chunk_blocks
from .embedder import Embedder
from .loaders import EmptyDocument, load_document
from .ollama_client import OllamaClient
from .prompts import NO_ANSWER, SYSTEM_PROMPT, build_messages
from .retriever import RetrievalConfig, retrieve
from .vectorstore import RetrievedChunk, VectorStore

CHARS_PER_TOKEN = 4
EventType = Literal["sources", "delta", "done"]


@dataclass(frozen=True, slots=True)
class KnowledgeBaseConfig:
    """Everything the engine needs to know about a knowledge base."""

    id: str
    embedding_model: str
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 4
    max_distance: float | None = 0.65

    def chunk_config(self) -> ChunkConfig:
        return ChunkConfig(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)


@dataclass(frozen=True, slots=True)
class IngestResult:
    document_id: str
    document_name: str
    chunks: int
    embedding_model: str
    pages: int | None = None


@dataclass(frozen=True, slots=True)
class StreamEvent:
    """One thing to send to the browser while an answer is produced."""

    type: EventType
    text: str = ""
    thinking: bool = False
    sources: tuple[RetrievedChunk, ...] = ()
    model: str = ""


def estimate_tokens(text: str) -> int:
    """Rough token count. Good enough for budgeting."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def ingest_document(
    path: str | Path,
    kb: KnowledgeBaseConfig,
    *,
    store: VectorStore,
    embedder: Embedder,
    document_id: str | None = None,
    document_name: str | None = None,
) -> IngestResult:
    """Load, chunk, embed and store one document."""
    target = Path(path)
    blocks = load_document(target)
    chunks = chunk_blocks(blocks, kb.chunk_config())
    if not chunks:
        raise EmptyDocument(f"{target.name} produced no chunks.")

    embeddings = embedder.embed_documents([chunk.text for chunk in chunks])
    doc_id = document_id or uuid4().hex
    name = document_name or target.name
    stored = store.add_chunks(
        kb.id,
        doc_id,
        chunks,
        embeddings,
        document_name=name,
    )
    pages = max((block.page for block in blocks if block.page is not None), default=None)
    return IngestResult(
        document_id=doc_id,
        document_name=name,
        chunks=stored,
        embedding_model=embedder.model,
        pages=pages,
    )


def _fit_chunks(chunks: Sequence[RetrievedChunk], budget: int) -> list[RetrievedChunk]:
    """Keep the best chunks that fit, never returning an empty list."""
    kept: list[RetrievedChunk] = []
    remaining = budget
    for chunk in chunks:
        cost = estimate_tokens(chunk.text) + 8
        if cost <= remaining:
            kept.append(chunk)
            remaining -= cost
        elif not kept:
            keep_chars = max(200, remaining * CHARS_PER_TOKEN)
            kept.append(replace(chunk, text=chunk.text[:keep_chars]))
            remaining = 0
        else:
            break
    return kept


def _fit_history(history: Sequence[dict[str, Any]], budget: int) -> list[dict[str, Any]]:
    """Keep the newest messages that fit."""
    kept: list[dict[str, Any]] = []
    used = 0
    for message in reversed(list(history)):
        cost = estimate_tokens(str(message.get("content", ""))) + 4
        if used + cost > budget:
            break
        kept.append(message)
        used += cost
    kept.reverse()
    return kept


def answer_stream(
    question: str,
    kb: KnowledgeBaseConfig,
    *,
    chat_model: str,
    client: OllamaClient,
    store: VectorStore,
    embedder: Embedder,
    history: Sequence[dict[str, Any]] = (),
    num_ctx: int = 8192,
    temperature: float = 0.2,
    think: bool | None = False,
    reserve_output_tokens: int = 1024,
    retrieval: RetrievalConfig | None = None,
) -> Iterator[StreamEvent]:
    """Retrieve, then stream the model's answer as events."""
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")

    config = retrieval or RetrievalConfig(top_k=kb.top_k, max_distance=kb.max_distance)
    found = retrieve(store, embedder, kb.id, question, config)

    budget = max(512, num_ctx - reserve_output_tokens)
    fixed = estimate_tokens(SYSTEM_PROMPT) + estimate_tokens(question) + 64
    history_messages = _fit_history(history, int(budget * 0.25))
    history_cost = sum(estimate_tokens(str(m.get("content", ""))) + 4 for m in history_messages)
    chunks = _fit_chunks(found, max(256, budget - fixed - history_cost))
    sources = tuple(chunks)

    if not chunks:
        yield StreamEvent(type="sources", sources=())
        yield StreamEvent(type="delta", text=NO_ANSWER)
        yield StreamEvent(type="done", text=NO_ANSWER, model=chat_model)
        return

    yield StreamEvent(type="sources", sources=sources)

    messages = build_messages(question, chunks, history_messages)
    options = {"num_ctx": num_ctx, "temperature": temperature}
    parts: list[str] = []
    for event in client.chat_stream(chat_model, messages, options=options, think=think):
        message = event.get("message") or {}
        reasoning = message.get("thinking")
        if reasoning:
            yield StreamEvent(type="delta", text=reasoning, thinking=True)
        content = message.get("content")
        if content:
            parts.append(content)
            yield StreamEvent(type="delta", text=content)

    yield StreamEvent(
        type="done",
        text="".join(parts).strip(),
        sources=sources,
        model=chat_model,
    )


def collect_answer(
    question: str,
    kb: KnowledgeBaseConfig,
    **kwargs: Any,
) -> tuple[str, tuple[RetrievedChunk, ...]]:
    """Non-streaming helper: run the pipeline and return (answer, sources)."""
    answer = ""
    sources: tuple[RetrievedChunk, ...] = ()
    for event in answer_stream(question, kb, **kwargs):
        if event.type == "sources":
            sources = event.sources
        elif event.type == "delta" and not event.thinking:
            answer += event.text
    return answer.strip(), sources

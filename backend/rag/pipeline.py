"""Ingest documents and answer questions. No Django in here."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterator, Literal, Sequence
from uuid import uuid4

from .chunking import ChunkConfig, chunk_blocks
from .embedder import Embedder
from .loaders import EmptyDocument, load_document
from .ollama_client import OllamaClient, OllamaError
from .prompts import NO_ANSWER, SYSTEM_PROMPT, build_messages
from .retriever import RetrievalConfig, retrieve
from .vectorstore import RetrievedChunk, VectorStore

CHARS_PER_TOKEN = 4
EventType = Literal["query", "sources", "delta", "done"]

# Words that usually point back at something said earlier.
REFERENCE_WORDS = frozenset(
    {
        "it", "its", "it's", "that", "this", "these", "those", "they", "them",
        "their", "theirs", "he", "she", "him", "her", "his", "hers",
        "one", "ones", "former", "latter", "above", "same", "previous", "earlier",
    }
)

# Questions that start like this rarely stand on their own.
FOLLOW_UP_STARTS = (
    "and ", "also ", "but ", "then ", "so ", "what about", "how about",
    "why", "explain", "elaborate", "tell me more", "more detail", "again",
    "simplify", "summarize more",
)

REWRITE_PROMPT = (
    "Rewrite the user's last message as one standalone search query. "
    "Use the earlier messages to replace pronouns and vague words. "
    "Reply with the query only. No quotes, no explanation."
)


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
    # Only set on "query" events: the question the user actually typed.
    original: str = ""


def estimate_tokens(text: str) -> int:
    """Rough token count. Good enough for budgeting."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def looks_like_follow_up(question: str) -> bool:
    """Cheap guess: does this sentence lean on earlier messages?

    Keeps the extra rewrite call off most questions.
    """
    text = question.strip().lower()
    if not text:
        return False
    words = re.findall(r"[a-z']+", text)
    if len(words) <= 3:
        return True
    if any(word in REFERENCE_WORDS for word in words):
        return True
    return text.startswith(FOLLOW_UP_STARTS)


def _tidy_rewrite(text: str, original: str) -> str:
    """Keep the first line, drop quotes; bail out if it looks wrong."""
    line = text.strip().splitlines()[0].strip() if text.strip() else ""
    line = line.strip("\"'` ")
    if line.lower().startswith("standalone query:"):
        line = line.split(":", 1)[1].strip()
    if not line or len(line) > 300:
        return original
    return line


def rewrite_query(
    question: str,
    history: Sequence[dict[str, Any]],
    *,
    client: OllamaClient,
    chat_model: str,
    num_ctx: int = 8192,
) -> str:
    """Turn a follow-up into a standalone query. Falls back to the original."""
    recent = [f"{m['role']}: {m['content']}" for m in list(history)[-6:]]
    prompt = (
        "Recent chat:\n"
        + "\n".join(recent)
        + f"\n\nLast message: {question}\n\nStandalone query:"
    )
    try:
        data = client.chat(
            chat_model,
            [
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": prompt},
            ],
            options={"num_ctx": num_ctx, "temperature": 0.0},
            think=False,
        )
    except OllamaError:
        # A missing rewrite is not worth failing the whole answer over.
        return question

    reply = (data.get("message") or {}).get("content") or ""
    return _tidy_rewrite(reply, question)


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
    rewrite_followups: bool = True,
    reserve_output_tokens: int = 1024,
    retrieval: RetrievalConfig | None = None,
) -> Iterator[StreamEvent]:
    """Retrieve, then stream the model's answer as events."""
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")

    # Follow-ups like "what about its limits?" retrieve badly as written.
    search_query = question
    if rewrite_followups and history and looks_like_follow_up(question):
        search_query = rewrite_query(
            question,
            history,
            client=client,
            chat_model=chat_model,
            # Same window as the answer, or Ollama reloads the model twice.
            num_ctx=num_ctx,
        )
        if search_query != question:
            yield StreamEvent(type="query", text=search_query, original=question)

    config = retrieval or RetrievalConfig(top_k=kb.top_k, max_distance=kb.max_distance)
    found = retrieve(store, embedder, kb.id, search_query, config)

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

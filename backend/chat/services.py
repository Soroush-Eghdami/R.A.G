"""Glue between chat views and the RAG engine."""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Sequence

from django.conf import settings
from django.utils import timezone
from kb.models import KnowledgeBase
from kb.services import build_client, build_embedder, build_store, config_for
from llm.models import AppSettings
from rag.ollama_client import OllamaClient
from rag.pipeline import StreamEvent, answer_stream
from rag.retriever import RetrievalConfig
from rag.vectorstore import RetrievedChunk, VectorStore

from .models import Conversation, Message


def build_runtime(kb: KnowledgeBase) -> tuple[OllamaClient, VectorStore, Any]:
    """Client, vector store and embedder for one knowledge base."""
    client = build_client()
    return client, build_store(), build_embedder(kb.embedding_model)


def citation(chunk: RetrievedChunk, number: int) -> dict[str, Any]:
    return {
        "n": number,
        "document_id": chunk.document_id,
        "document": chunk.document_name,
        "page": chunk.page,
        "distance": round(chunk.distance, 4),
        "snippet": chunk.text[:300],
    }


def sources_payload(chunks: Sequence[RetrievedChunk]) -> list[dict[str, Any]]:
    """Citation blocks sent to the UI."""
    return [citation(chunk, number) for number, chunk in enumerate(chunks, start=1)]


def search_payload(chunks: Sequence[RetrievedChunk]) -> list[dict[str, Any]]:
    """Same as citations, plus the full chunk text."""
    return [
        {**citation(chunk, number), "text": chunk.text}
        for number, chunk in enumerate(chunks, start=1)
    ]


def conversation_history(conversation: Conversation, *, limit: int = 20) -> list[dict]:
    """Recent messages, oldest first. The pipeline trims by token budget."""
    recent = list(conversation.messages.order_by("-created_at")[:limit])
    recent.reverse()
    return [
        {"role": message.role, "content": message.content}
        for message in recent
        if message.content
    ]


def pipeline_options(
    conversation: Conversation,
    history: Sequence[dict[str, Any]],
    data: dict[str, Any],
) -> dict[str, Any]:
    """App defaults plus per-request overrides."""
    defaults = AppSettings.load()
    return {
        "history": list(history),
        "num_ctx": data.get("num_ctx") or defaults.num_ctx,
        "temperature": defaults.temperature,
        "think": data.get("think", settings.DEFAULT_THINK),
        "rewrite_followups": settings.REWRITE_FOLLOWUPS,
        "retrieval": RetrievalConfig(top_k=data.get("top_k") or defaults.top_k),
    }


def stream_answer(
    conversation: Conversation,
    question: str,
    *,
    options: dict[str, Any],
) -> Iterator[StreamEvent]:
    """Run the pipeline for a conversation."""
    client, store, embedder = build_runtime(conversation.knowledge_base)
    yield from answer_stream(
        question,
        config_for(conversation.knowledge_base),
        chat_model=conversation.chat_model,
        client=client,
        store=store,
        embedder=embedder,
        **options,
    )


def save_message(
    conversation: Conversation,
    role: str,
    content: str,
    *,
    sources: Iterable[dict[str, Any]] = (),
    model_used: str = "",
) -> Message:
    message = Message.objects.create(
        conversation=conversation,
        role=role,
        content=content,
        sources=list(sources),
        model_used=model_used,
    )
    Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
    return message


def title_from(question: str) -> str:
    return question.strip()[:80]

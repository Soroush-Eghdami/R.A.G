"""Build llama.cpp clients and report configured models and server health."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import connection
from rag.llama_cpp_client import LlamaCppClient, LLMError
from rag.model_registry import ModelInfo


def build_chat_client() -> LlamaCppClient:
    return LlamaCppClient(
        settings.LLAMA_CPP_CHAT_BASE_URL,
        connect_timeout=settings.LLAMA_CPP_CONNECT_TIMEOUT,
        request_timeout=settings.LLAMA_CPP_REQUEST_TIMEOUT,
    )


def build_embedding_client() -> LlamaCppClient:
    return LlamaCppClient(
        settings.LLAMA_CPP_EMBEDDING_BASE_URL,
        connect_timeout=settings.LLAMA_CPP_CONNECT_TIMEOUT,
        request_timeout=settings.LLAMA_CPP_REQUEST_TIMEOUT,
    )


def visible_models(*, force: bool = False) -> tuple[list[ModelInfo], int, str]:
    """Return configured chat/embedding aliases and their server addresses."""
    del force
    models = [
        ModelInfo(
            name=settings.LLAMA_CPP_CHAT_MODEL,
            kind="chat",
            capabilities=("completion",),
        ),
        ModelInfo(
            name=settings.LLAMA_CPP_EMBEDDING_MODEL,
            kind="embedding",
            capabilities=("embedding",),
        ),
    ]
    return models, 0, settings.LLAMA_CPP_CHAT_BASE_URL


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:  # noqa: BLE001 - health checks must never raise
        return False


def _server_health(client: LlamaCppClient) -> dict[str, Any]:
    try:
        client.health()
        return {"reachable": True, "base_url": client.base_url, "error": None}
    except LLMError as exc:
        return {"reachable": False, "base_url": client.base_url, "error": str(exc)}


def get_health() -> dict[str, Any]:
    """Report each model server and the database without raising."""
    chat = _server_health(build_chat_client())
    embedding = _server_health(build_embedding_client())
    database_ok = _database_ok()
    healthy = chat["reachable"] and embedding["reachable"] and database_ok
    return {
        "status": "ok" if healthy else "degraded",
        "chat": chat,
        "embedding": embedding,
        "database": {"ok": database_ok},
    }

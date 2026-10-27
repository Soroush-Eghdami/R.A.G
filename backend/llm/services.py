"""Django-facing glue for the Ollama model layer.

Keeps the framework-free ``rag`` package unaware of Django settings and turns
its typed errors into API-friendly data.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import connection
from rag.model_registry import ModelInfo, discover_models
from rag.ollama_client import OllamaClient, OllamaError


def build_client() -> OllamaClient:
    """Create a client using deployment configuration from settings/.env."""
    return OllamaClient(
        settings.OLLAMA_BASE_URL,
        connect_timeout=settings.OLLAMA_CONNECT_TIMEOUT,
        request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
    )


def visible_models(*, force: bool = False) -> tuple[list[ModelInfo], int, str]:
    """Return (visible models, hidden cloud count, base url)."""
    client = build_client()
    models = discover_models(
        client,
        force=force,
        ttl=settings.MODEL_CACHE_TTL,
    )
    if settings.SHOW_CLOUD_MODELS:
        return models, 0, client.base_url

    visible = [model for model in models if not model.is_cloud]
    hidden = len(models) - len(visible)
    return visible, hidden, client.base_url


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:  # noqa: BLE001 - health checks must never raise
        return False


def get_health() -> dict[str, Any]:
    """Report Django/DB and Ollama status without ever raising."""
    client = build_client()
    try:
        version = client.version()
        ollama: dict[str, Any] = {
            "reachable": True,
            "version": version,
            "base_url": client.base_url,
            "error": None,
        }
    except OllamaError as exc:
        ollama = {
            "reachable": False,
            "version": None,
            "base_url": client.base_url,
            "error": str(exc),
        }

    database_ok = _database_ok()
    healthy = bool(ollama["reachable"]) and database_ok
    return {
        "status": "ok" if healthy else "degraded",
        "ollama": ollama,
        "database": {"ok": database_ok},
    }

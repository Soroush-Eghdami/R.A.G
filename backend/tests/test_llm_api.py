"""API tests for configured llama.cpp models and model-server health."""

from __future__ import annotations

import httpx
import pytest
import respx
from django.test import override_settings

pytestmark = pytest.mark.django_db

CHAT = "http://llama-chat.test:8082"
EMBEDDING = "http://llama-embedding.test:8083"
CHAT_DOWN = "http://llama-chat-down.test:8082"
EMBEDDING_DOWN = "http://llama-embedding-down.test:8083"


@override_settings(
    LLAMA_CPP_CHAT_BASE_URL=CHAT,
    LLAMA_CPP_EMBEDDING_BASE_URL=EMBEDDING,
    LLAMA_CPP_CHAT_MODEL="Qwen3.5-9B",
    LLAMA_CPP_EMBEDDING_MODEL="nomic-embed-text-v1.5",
)
def test_models_returns_configured_aliases(client):
    response = client.get("/api/models/")
    assert response.status_code == 200
    body = response.json()
    assert [model["name"] for model in body["chat"]] == ["Qwen3.5-9B"]
    assert [model["name"] for model in body["embedding"]] == ["nomic-embed-text-v1.5"]
    assert body["chat_base_url"] == CHAT
    assert body["embedding_base_url"] == EMBEDDING


@override_settings(LLAMA_CPP_CHAT_BASE_URL=CHAT, LLAMA_CPP_EMBEDDING_BASE_URL=EMBEDDING)
@respx.mock
def test_health_reports_both_servers(client):
    respx.get(f"{CHAT}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx.get(f"{EMBEDDING}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["chat"]["reachable"] is True
    assert body["embedding"]["reachable"] is True
    assert body["database"]["ok"] is True


@override_settings(
    LLAMA_CPP_CHAT_BASE_URL=CHAT_DOWN,
    LLAMA_CPP_EMBEDDING_BASE_URL=EMBEDDING,
    LLAMA_CPP_CONNECT_TIMEOUT=0.2,
)
@respx.mock
def test_health_degrades_when_one_server_is_down(client):
    respx.get(f"{CHAT_DOWN}/health").mock(
        return_value=httpx.Response(503, json={"error": "server loading"})
    )
    respx.get(f"{EMBEDDING}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["chat"]["reachable"] is False
    assert body["embedding"]["reachable"] is True
    assert body["chat"]["error"]


@override_settings(
    LLAMA_CPP_CHAT_BASE_URL=CHAT,
    LLAMA_CPP_EMBEDDING_BASE_URL=EMBEDDING_DOWN,
    LLAMA_CPP_CONNECT_TIMEOUT=0.2,
)
@respx.mock
def test_health_degrades_when_embedding_server_is_down(client):
    respx.get(f"{CHAT}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx.get(f"{EMBEDDING_DOWN}/health").mock(
        return_value=httpx.Response(503, json={"error": "server loading"})
    )
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["chat"]["reachable"] is True
    assert body["embedding"]["reachable"] is False

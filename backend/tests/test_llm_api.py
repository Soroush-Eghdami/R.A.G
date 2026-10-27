"""API tests for /api/health/ and /api/models/ with a mocked Ollama."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from django.test import override_settings
from rag.model_registry import clear_model_cache

pytestmark = pytest.mark.django_db

BASE = "http://ollama.test:11434"

TAGS = {
    "models": [
        {
            "name": "qwen3.5:9b",
            "size": 6_600_000_000,
            "details": {
                "family": "qwen35",
                "parameter_size": "9.0B",
                "quantization_level": "Q4_K_M",
            },
        },
        {
            "name": "kimi-k3:cloud",
            "size": 0,
            "details": {"family": "kimi"},
        },
        {
            "name": "nomic-embed-text:latest",
            "size": 274_000_000,
            "details": {
                "family": "nomic-bert",
                "parameter_size": "137M",
                "quantization_level": "F16",
            },
        },
        {
            "name": "all-minilm:latest",
            "size": 45_000_000,
            "details": {"family": "llama", "parameter_size": "23M"},
        },
    ]
}

SHOWS = {
    "qwen3.5:9b": {
        "capabilities": ["completion", "vision", "thinking"],
        "model_info": {"qwen35.context_length": 262144},
    },
    "kimi-k3:cloud": {"capabilities": ["completion"], "model_info": {}},
    "nomic-embed-text:latest": {
        "capabilities": ["embedding"],
        "model_info": {"nomic-bert.context_length": 2048},
    },
    "all-minilm:latest": {"capabilities": ["embedding"]},
}


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_model_cache()
    yield
    clear_model_cache()


def _show(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    return httpx.Response(200, json=SHOWS.get(payload["model"], {}))


@override_settings(OLLAMA_BASE_URL=BASE, SHOW_CLOUD_MODELS=False)
@respx.mock
def test_models_split_and_hide_cloud(client):
    respx.get(f"{BASE}/api/tags").mock(return_value=httpx.Response(200, json=TAGS))
    respx.post(f"{BASE}/api/show").mock(side_effect=_show)

    response = client.get("/api/models/")
    assert response.status_code == 200
    data = response.json()

    assert [model["name"] for model in data["chat"]] == ["qwen3.5:9b"]
    assert [model["name"] for model in data["embedding"]] == [
        "all-minilm:latest",
        "nomic-embed-text:latest",
    ]
    assert data["cloud_hidden"] == 1
    assert data["base_url"] == BASE

    qwen = data["chat"][0]
    assert qwen["kind"] == "chat"
    assert qwen["context_length"] == 262144
    assert "thinking" in qwen["capabilities"]


@override_settings(OLLAMA_BASE_URL=BASE, SHOW_CLOUD_MODELS=True)
@respx.mock
def test_models_include_cloud_when_enabled(client):
    respx.get(f"{BASE}/api/tags").mock(return_value=httpx.Response(200, json=TAGS))
    respx.post(f"{BASE}/api/show").mock(side_effect=_show)

    response = client.get("/api/models/")
    data = response.json()

    assert [model["name"] for model in data["chat"]] == ["kimi-k3:cloud", "qwen3.5:9b"]
    assert data["cloud_hidden"] == 0


@override_settings(OLLAMA_BASE_URL=BASE)
@respx.mock
def test_models_empty_list(client):
    respx.get(f"{BASE}/api/tags").mock(
        return_value=httpx.Response(200, json={"models": []})
    )
    response = client.get("/api/models/")
    assert response.status_code == 200
    assert response.json()["chat"] == []
    assert response.json()["embedding"] == []


@override_settings(
    OLLAMA_BASE_URL="http://127.0.0.1:1",
    OLLAMA_CONNECT_TIMEOUT=0.2,
    MODEL_CACHE_TTL=0,
)
def test_models_returns_503_when_ollama_is_down(client):
    response = client.get("/api/models/")
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "ollama_unavailable"
    assert "Could not reach Ollama" in body["detail"]


@override_settings(OLLAMA_BASE_URL=BASE)
@respx.mock
def test_models_returns_502_on_unexpected_ollama_error(client):
    respx.get(f"{BASE}/api/tags").mock(
        return_value=httpx.Response(400, json={"error": "bad request"})
    )
    response = client.get("/api/models/")
    assert response.status_code == 502
    assert response.json()["code"] == "ollama_response_error"


@override_settings(OLLAMA_BASE_URL=BASE)
@respx.mock
def test_health_when_ollama_is_up(client):
    respx.get(f"{BASE}/api/version").mock(
        return_value=httpx.Response(200, json={"version": "0.40.10"})
    )
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ollama"]["reachable"] is True
    assert body["ollama"]["version"] == "0.40.10"
    assert body["database"]["ok"] is True


@override_settings(
    OLLAMA_BASE_URL="http://127.0.0.1:1",
    OLLAMA_CONNECT_TIMEOUT=0.2,
)
def test_health_degrades_when_ollama_is_down(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["ollama"]["reachable"] is False
    assert body["ollama"]["error"]


@override_settings(OLLAMA_BASE_URL=BASE)
@respx.mock
def test_models_cache_is_reused(client):
    tags_route = respx.get(f"{BASE}/api/tags").mock(
        return_value=httpx.Response(200, json=TAGS)
    )
    respx.post(f"{BASE}/api/show").mock(side_effect=_show)

    assert client.get("/api/models/").status_code == 200
    assert client.get("/api/models/").status_code == 200
    assert tags_route.call_count == 1

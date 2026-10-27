"""Tests for the typed Ollama HTTP client."""

from __future__ import annotations

import httpx
import pytest
import respx
from rag.ollama_client import (
    ModelNotFound,
    OllamaClient,
    OllamaResponseError,
    OllamaUnavailable,
)

BASE = "http://ollama.test:11434"


@pytest.fixture
def client():
    return OllamaClient(BASE, connect_timeout=0.2, request_timeout=5.0)


@respx.mock
def test_version(client):
    respx.get(f"{BASE}/api/version").mock(
        return_value=httpx.Response(200, json={"version": "0.40.10"})
    )
    assert client.version() == "0.40.10"


@respx.mock
def test_list_models(client):
    respx.get(f"{BASE}/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={"models": [{"name": "qwen3.5:9b"}, {"name": "nomic-embed-text"}]},
        )
    )
    assert [m["name"] for m in client.list_models()] == [
        "qwen3.5:9b",
        "nomic-embed-text",
    ]


@respx.mock
def test_show_model_not_found(client):
    respx.post(f"{BASE}/api/show").mock(
        return_value=httpx.Response(404, json={"error": "model 'nope' not found"})
    )
    with pytest.raises(ModelNotFound) as excinfo:
        client.show_model("nope")
    assert excinfo.value.status_code == 404
    assert "nope" in str(excinfo.value)


@respx.mock
def test_embed_returns_batch(client):
    respx.post(f"{BASE}/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
    )
    embeddings = client.embed("nomic-embed-text", ["a", "b"])
    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]


@respx.mock
def test_embed_rejects_mismatched_batch(client):
    respx.post(f"{BASE}/api/embed").mock(
        return_value=httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})
    )
    with pytest.raises(OllamaResponseError):
        client.embed("nomic-embed-text", ["a", "b"])


@respx.mock
def test_chat_stream_parses_ndjson(client):
    body = (
        b'{"message": {"content": "Hel"}, "done": false}\n'
        b'{"message": {"thinking": "hm"}, "done": false}\n'
        b'{"message": {"content": "lo"}, "done": false}\n'
        b'{"done": true}\n'
    )
    respx.post(f"{BASE}/api/chat").mock(
        return_value=httpx.Response(200, content=body)
    )

    events = list(client.chat_stream("qwen3.5:9b", [{"role": "user", "content": "hi"}]))
    text = "".join(e.get("message", {}).get("content", "") for e in events)
    thinking = "".join(e.get("message", {}).get("thinking", "") for e in events)
    assert text == "Hello"
    assert thinking == "hm"
    assert events[-1]["done"] is True


@respx.mock
def test_server_error_is_reported(client):
    respx.get(f"{BASE}/api/tags").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    with pytest.raises(OllamaUnavailable):
        client.list_models()


def test_unreachable_ollama_raises_typed_error():
    client = OllamaClient("http://127.0.0.1:1", connect_timeout=0.2, request_timeout=1.0)
    with pytest.raises(OllamaUnavailable):
        client.version()

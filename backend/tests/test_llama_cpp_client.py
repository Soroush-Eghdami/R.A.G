"""Tests for the llama.cpp OpenAI-compatible HTTP client."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from rag.llama_cpp_client import (
    LlamaCppClient,
    LLMResponseError,
    LLMUnavailable,
    ModelNotFound,
)

BASE = "http://llama.test:8082"


@pytest.fixture
def client():
    return LlamaCppClient(BASE, connect_timeout=0.2, request_timeout=5.0)


@respx.mock
def test_health(client):
    respx.get(f"{BASE}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.health()


@respx.mock
def test_embedding_batch_is_returned_in_input_order(client):
    route = respx.post(f"{BASE}/v1/embeddings").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.3, 0.4]},
                    {"index": 0, "embedding": [0.1, 0.2]},
                ]
            },
        )
    )
    embeddings = client.embed("nomic-embed-text-v1.5", ["first", "second"])
    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert json.loads(route.calls[0].request.content)["input"] == ["first", "second"]


@respx.mock
def test_embedding_rejects_missing_vectors(client):
    respx.post(f"{BASE}/v1/embeddings").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    with pytest.raises(LLMResponseError):
        client.embed("nomic-embed-text-v1.5", ["first"])


@respx.mock
def test_chat_normalizes_openai_response(client):
    route = respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "Answer.",
                            "reasoning_content": "Reasoning.",
                        }
                    }
                ]
            },
        )
    )
    result = client.chat(
        "Qwen3.5-9B",
        [{"role": "user", "content": "Question"}],
        options={"temperature": 0.2, "num_ctx": 4096},
        think=True,
    )
    assert result["message"] == {"content": "Answer.", "thinking": "Reasoning."}
    payload = json.loads(route.calls[0].request.content)
    assert payload["temperature"] == 0.2
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}
    assert "num_ctx" not in payload


@respx.mock
def test_chat_stream_parses_sse_and_reasoning(client):
    body = (
        b'data: {"choices":[{"delta":{"reasoning_content":"think"}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
        b'data: {"choices":[{"delta":{"content":"!"},"finish_reason":"stop"}]}\n\n'
        b"data: [DONE]\n\n"
    )
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=body)
    )
    events = list(
        client.chat_stream("Qwen3.5-9B", [{"role": "user", "content": "Hi"}])
    )
    assert events == [
        {"message": {"thinking": "think"}},
        {"message": {"content": "Hello"}},
        {"message": {"content": "!"}},
        {"done": True},
    ]


@respx.mock
def test_missing_model_is_typed(client):
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(404, json={"error": {"message": "model not found"}})
    )
    with pytest.raises(ModelNotFound):
        client.chat("missing-model", [{"role": "user", "content": "Hi"}])


@respx.mock
def test_malformed_stream_is_reported(client):
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=b"data: {bad json}\n\n")
    )
    with pytest.raises(LLMResponseError):
        list(client.chat_stream("Qwen3.5-9B", []))


def test_unreachable_server_raises_typed_error():
    client = LlamaCppClient(
        "http://127.0.0.1:1",
        connect_timeout=0.2,
        request_timeout=1.0,
    )
    with pytest.raises(LLMUnavailable):
        client.health()

"""Embedder tests, no Ollama needed."""

from __future__ import annotations

import pytest
from rag.embedder import OllamaEmbedder, prefixes_for
from rag.ollama_client import OllamaResponseError


class FakeClient:
    def __init__(self):
        self.calls = []

    def embed(self, model, texts):
        self.calls.append((model, list(texts)))
        return [[float(len(text))] for text in texts]


def test_nomic_prefixes():
    assert prefixes_for("nomic-embed-text:latest") == (
        "search_document: ",
        "search_query: ",
    )


def test_unknown_model_has_no_prefixes():
    assert prefixes_for("all-minilm:latest") == ("", "")


def test_documents_are_batched_and_prefixed():
    client = FakeClient()
    embedder = OllamaEmbedder(client, "nomic-embed-text:latest", batch_size=2)
    vectors = embedder.embed_documents(["one", "two", "three"])

    assert len(vectors) == 3
    assert [len(call[1]) for call in client.calls] == [2, 1]
    assert client.calls[0][1][0].startswith("search_document: ")


def test_query_uses_query_prefix():
    client = FakeClient()
    embedder = OllamaEmbedder(client, "nomic-embed-text:latest")
    embedder.embed_query("why?")
    assert client.calls[0][1] == ["search_query: why?"]


def test_empty_document_list_skips_http():
    client = FakeClient()
    assert OllamaEmbedder(client, "m").embed_documents([]) == []
    assert client.calls == []


def test_mismatched_vector_count_raises():
    class ShortClient:
        def embed(self, model, texts):
            return [[0.1]]

    embedder = OllamaEmbedder(ShortClient(), "m")
    with pytest.raises(OllamaResponseError):
        embedder.embed_documents(["a", "b"])

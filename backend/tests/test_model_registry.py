"""Unit tests for model classification and the discovery cache."""

from __future__ import annotations

import pytest
from rag.model_registry import (
    ModelInfo,
    classify_model,
    clear_model_cache,
    discover_models,
    is_cloud_model,
)
from rag.ollama_client import ModelNotFound


class FakeClient:
    base_url = "http://fake-ollama:11434"

    def __init__(self, models, shows, missing=()):
        self._models = models
        self._shows = shows
        self._missing = set(missing)
        self.list_calls = 0
        self.show_calls = 0

    def list_models(self):
        self.list_calls += 1
        return self._models

    def show_model(self, name):
        self.show_calls += 1
        if name in self._missing:
            raise ModelNotFound(f"Model '{name}' is not installed.")
        return self._shows.get(name, {})


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_model_cache()
    yield
    clear_model_cache()


def _raw(name, size=100, family="llama"):
    return {
        "name": name,
        "size": size,
        "details": {
            "family": family,
            "parameter_size": "9B",
            "quantization_level": "Q4_K_M",
        },
    }


def test_classify_by_capabilities():
    assert classify_model("qwen3.5:9b", ["completion", "thinking"]) == "chat"
    assert classify_model("nomic-embed-text", ["embedding"]) == "embedding"


def test_classify_falls_back_to_name_when_capabilities_missing():
    assert classify_model("all-minilm:latest", []) == "embedding"
    assert classify_model("nomic-embed-text:latest", []) == "embedding"
    assert classify_model("llama3.2:3b", []) == "chat"


def test_cloud_detection():
    assert is_cloud_model("kimi-k3:cloud")
    assert is_cloud_model("qwen3:cloud")
    assert not is_cloud_model("qwen3.5:9b")


def test_discover_models_classifies_and_extracts_context():
    client = FakeClient(
        models=[
            _raw("qwen3.5:9b"),
            _raw("nomic-embed-text:latest", size=123, family="nomic-bert"),
            _raw("kimi-k3:cloud", size=0),
        ],
        shows={
            "qwen3.5:9b": {
                "capabilities": ["completion", "vision", "thinking"],
                "model_info": {"qwen35.context_length": 262144},
            },
            "nomic-embed-text:latest": {"capabilities": ["embedding"]},
            "kimi-k3:cloud": {"capabilities": ["completion"]},
        },
    )

    models = discover_models(client, force=True)
    by_name = {model.name: model for model in models}

    assert by_name["qwen3.5:9b"].kind == "chat"
    assert by_name["qwen3.5:9b"].context_length == 262144
    assert "thinking" in by_name["qwen3.5:9b"].capabilities
    assert by_name["nomic-embed-text:latest"].kind == "embedding"
    assert by_name["kimi-k3:cloud"].is_cloud is True
    assert all(isinstance(model, ModelInfo) for model in models)


def test_discovery_cache_avoids_repeated_http_calls():
    client = FakeClient(
        models=[_raw("qwen3.5:9b")],
        shows={"qwen3.5:9b": {"capabilities": ["completion"]}},
    )

    discover_models(client, ttl=30)
    discover_models(client, ttl=30)
    assert client.list_calls == 1
    assert client.show_calls == 1

    discover_models(client, force=True, ttl=30)
    assert client.list_calls == 2


def test_ttl_zero_disables_cache():
    client = FakeClient(
        models=[_raw("qwen3.5:9b")],
        shows={"qwen3.5:9b": {"capabilities": ["completion"]}},
    )
    discover_models(client, ttl=0)
    discover_models(client, ttl=0)
    assert client.list_calls == 2


def test_missing_show_metadata_falls_back_to_heuristics():
    client = FakeClient(
        models=[_raw("all-minilm:latest"), _raw("llama3.2:3b")],
        shows={},
        missing={"all-minilm:latest"},
    )

    models = {model.name: model for model in discover_models(client, force=True)}
    assert models["all-minilm:latest"].kind == "embedding"
    assert models["llama3.2:3b"].kind == "chat"

"""List and classify Ollama models.

Uses capabilities from /api/show, with a name heuristic for older versions.
The result is cached for 30s because each model costs one /api/show call.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Literal

from .ollama_client import OllamaClient, OllamaError, OllamaTimeout, OllamaUnavailable

ModelKind = Literal["chat", "embedding"]

# Used only when /api/show does not report capabilities (older Ollama).
EMBEDDING_NAME_HINTS = (
    "embed",
    "minilm",
    "bge",
    "nomic",
    "mxbai",
    "arctic-embed",
    "e5-",
    "gte-",
    "jina",
)

DEFAULT_CACHE_TTL = 30.0

_lock = threading.Lock()
_cache: dict[str, tuple[float, tuple[ModelInfo, ...]]] = {}


@dataclass(frozen=True)
class ModelInfo:
    """Normalized view of an installed Ollama model."""

    name: str
    kind: ModelKind
    capabilities: tuple[str, ...] = ()
    size_bytes: int = 0
    parameter_size: str = ""
    quantization: str = ""
    family: str = ""
    context_length: int | None = None
    is_cloud: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "capabilities": list(self.capabilities),
            "size_bytes": self.size_bytes,
            "parameter_size": self.parameter_size,
            "quantization": self.quantization,
            "family": self.family,
            "context_length": self.context_length,
            "is_cloud": self.is_cloud,
        }


def clear_model_cache(base_url: str | None = None) -> None:
    """Drop cached models (all of them, or one server). Used by tests/refresh."""
    with _lock:
        if base_url is None:
            _cache.clear()
        else:
            _cache.pop(base_url.rstrip("/"), None)


def is_cloud_model(name: str) -> bool:
    """Ollama cloud models use the ``:cloud`` tag (e.g. kimi-k3:cloud)."""
    lowered = name.lower()
    return lowered.endswith(":cloud") or lowered.endswith("-cloud")


def classify_model(name: str, capabilities: list[str] | tuple[str, ...]) -> ModelKind:
    """Decide whether a model is for chat or embeddings."""
    caps = {capability.lower() for capability in capabilities}
    if "embedding" in caps and "completion" not in caps:
        return "embedding"
    if "completion" in caps:
        return "chat"

    lowered = name.lower()
    if any(hint in lowered for hint in EMBEDDING_NAME_HINTS):
        return "embedding"
    return "chat"


def _extract_context_length(model_info: dict[str, Any]) -> int | None:
    """Read ``<architecture>.context_length`` (qwen35.context_length, ...)."""
    direct = model_info.get("context_length")
    if isinstance(direct, int) and direct > 0:
        return direct
    for key, value in model_info.items():
        if key.endswith(".context_length") and isinstance(value, int) and value > 0:
            return value
    return None


def _build_model_info(
    raw: dict[str, Any],
    show: dict[str, Any],
) -> ModelInfo:
    name = str(raw.get("name") or raw.get("model") or "").strip()
    details = raw.get("details") or {}
    if not isinstance(details, dict):
        details = {}

    raw_capabilities = show.get("capabilities") or []
    capabilities = tuple(
        str(capability) for capability in raw_capabilities if isinstance(capability, str)
    )

    model_info = show.get("model_info") or {}
    if not isinstance(model_info, dict):
        model_info = {}

    return ModelInfo(
        name=name,
        kind=classify_model(name, capabilities),
        capabilities=capabilities,
        size_bytes=int(raw.get("size") or 0),
        parameter_size=str(details.get("parameter_size") or ""),
        quantization=str(details.get("quantization_level") or ""),
        family=str(details.get("family") or ""),
        context_length=_extract_context_length(model_info),
        is_cloud=is_cloud_model(name),
    )


def discover_models(
    client: OllamaClient,
    *,
    force: bool = False,
    ttl: float = DEFAULT_CACHE_TTL,
) -> list[ModelInfo]:
    """List installed models with capabilities, using a short-lived cache."""
    cache_key = client.base_url
    now = time.monotonic()

    if not force and ttl > 0:
        with _lock:
            cached = _cache.get(cache_key)
        if cached and now - cached[0] < ttl:
            return list(cached[1])

    raw_models = client.list_models()
    discovered: list[ModelInfo] = []
    for raw in raw_models:
        name = str(raw.get("name") or raw.get("model") or "").strip()
        if not name:
            continue
        try:
            show = client.show_model(name)
        except (OllamaUnavailable, OllamaTimeout):
            # The server died mid-discovery; do not cache a partial list.
            raise
        except OllamaError:
            # A single model disappeared or misbehaved; fall back to heuristics.
            show = {}
        discovered.append(_build_model_info(raw, show))

    discovered.sort(key=lambda model: (model.kind, model.name.lower()))

    if ttl > 0:
        with _lock:
            _cache[cache_key] = (now, tuple(discovered))
    return discovered

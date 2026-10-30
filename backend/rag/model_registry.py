"""Configured llama.cpp model identities exposed by the API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ModelKind = Literal["chat", "embedding"]


@dataclass(frozen=True)
class ModelInfo:
    """Normalized model entry for the frontend model selectors."""

    name: str
    kind: ModelKind
    capabilities: tuple[str, ...] = ()
    size_bytes: int = 0
    parameter_size: str = ""
    quantization: str = ""
    family: str = "llama.cpp"
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

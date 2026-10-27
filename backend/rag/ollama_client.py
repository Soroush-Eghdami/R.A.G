"""Typed wrapper around the Ollama HTTP API. No Django in here.

Errors are normalized so views can map them to status codes:
unavailable/timeout -> 503, model missing -> 409, unexpected -> 502.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx


class OllamaError(Exception):
    """Base class for every Ollama failure."""

    code = "ollama_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class OllamaUnavailable(OllamaError):
    """Ollama is not running, or the connection was refused."""

    code = "ollama_unavailable"


class OllamaTimeout(OllamaUnavailable):
    """Ollama accepted the connection but did not answer in time."""

    code = "ollama_timeout"


class ModelNotFound(OllamaError):
    """The requested model is not installed in Ollama."""

    code = "model_not_found"


class OllamaResponseError(OllamaError):
    """Ollama returned an error status or an unexpected payload."""

    code = "ollama_response_error"


class OllamaClient:
    """Minimal client for the Ollama endpoints this app uses."""

    def __init__(
        self,
        base_url: str,
        *,
        connect_timeout: float = 5.0,
        request_timeout: float = 600.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self._timeout = httpx.Timeout(request_timeout, connect=connect_timeout)
        # Health checks must fail fast: the UI polls them.
        self._health_timeout = httpx.Timeout(
            min(5.0, request_timeout), connect=connect_timeout
        )

    # ------------------------------------------------------------------
    # Low level
    # ------------------------------------------------------------------

    def _unavailable_message(self) -> str:
        return (
            f"Could not reach Ollama at {self.base_url}. "
            "Start it with 'ollama serve' and try again."
        )

    def _raise_response(self, response: httpx.Response, *, model: str | None) -> None:
        detail = ""
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            detail = str(payload.get("error") or payload.get("detail") or "")

        if response.status_code == 404 and (
            model is not None or "not found" in detail.lower()
        ):
            raise ModelNotFound(
                f"Model '{model}' is not installed in Ollama."
                if model
                else (detail or "Resource not found."),
                status_code=response.status_code,
                detail=detail,
            )
        if response.status_code >= 500:
            raise OllamaUnavailable(
                f"Ollama at {self.base_url} reported a server error: "
                f"{detail or response.status_code}.",
                status_code=response.status_code,
                detail=detail,
            )
        raise OllamaResponseError(
            detail or f"Ollama returned HTTP {response.status_code}.",
            status_code=response.status_code,
            detail=detail,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        model: str | None = None,
        timeout: httpx.Timeout | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            with httpx.Client(
                base_url=self.base_url, timeout=timeout or self._timeout
            ) as client:
                response = client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaUnavailable(self._unavailable_message()) from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            raise OllamaTimeout(
                f"Ollama at {self.base_url} timed out. "
                "The model may still be loading; try again."
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(
                f"Could not talk to Ollama at {self.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            self._raise_response(response, model=model)
        return response

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    def version(self) -> str | None:
        """Return the Ollama version string, or None if it does not report one."""
        response = self._request("GET", "/api/version", timeout=self._health_timeout)
        data = response.json()
        return data.get("version") if isinstance(data, dict) else None

    def list_models(self) -> list[dict[str, Any]]:
        """Return the raw entries from ``GET /api/tags``."""
        response = self._request("GET", "/api/tags", timeout=self._health_timeout)
        data = response.json()
        models = data.get("models", []) if isinstance(data, dict) else []
        return [m for m in models if isinstance(m, dict)]

    def show_model(self, name: str) -> dict[str, Any]:
        """Return metadata/capabilities for one model (``POST /api/show``)."""
        response = self._request(
            "POST", "/api/show", json={"model": name}, model=name
        )
        data = response.json()
        return data if isinstance(data, dict) else {}

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts with Ollama's batch endpoint."""
        if not texts:
            return []
        response = self._request(
            "POST",
            "/api/embed",
            json={"model": model, "input": list(texts)},
            model=model,
        )
        data = response.json()
        embeddings = data.get("embeddings") if isinstance(data, dict) else None
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaResponseError(
                f"Ollama returned {len(embeddings or [])} embeddings for "
                f"{len(texts)} inputs.",
                detail=str(data)[:500],
            )
        return embeddings

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> dict[str, Any]:
        """Run a non-streaming chat completion and return the raw payload."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options:
            payload["options"] = options
        if think is not None:
            payload["think"] = think

        response = self._request("POST", "/api/chat", json=payload, model=model)
        data = response.json()
        if not isinstance(data, dict):
            raise OllamaResponseError("Ollama returned an unexpected chat payload.")
        return data

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield NDJSON events. The last one has ``done: true``."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if options:
            payload["options"] = options
        if think is not None:
            payload["think"] = think

        try:
            with httpx.Client(base_url=self.base_url, timeout=self._timeout) as client:
                with client.stream("POST", "/api/chat", json=payload) as response:
                    if response.status_code >= 400:
                        response.read()
                        self._raise_response(response, model=model)
                    for line in response.iter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(event, dict):
                            yield event
                            if event.get("done"):
                                return
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise OllamaUnavailable(self._unavailable_message()) from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            raise OllamaTimeout(
                f"Ollama stopped responding at {self.base_url}. "
                "The model may have been unloaded."
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailable(
                f"Connection to Ollama at {self.base_url} failed: {exc}"
            ) from exc

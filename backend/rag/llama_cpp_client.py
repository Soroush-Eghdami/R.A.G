"""HTTP client for llama.cpp's OpenAI-compatible server API."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx


class LLMError(Exception):
    """Base class for llama.cpp server failures."""

    code = "llm_error"

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


class LLMUnavailable(LLMError):
    """The llama.cpp server is not running or cannot be reached."""

    code = "llm_unavailable"


class LLMTimeout(LLMUnavailable):
    """The llama.cpp server did not respond before the request timed out."""

    code = "llm_timeout"


class ModelNotFound(LLMError):
    """The requested model is not loaded by the llama.cpp server."""

    code = "model_not_found"


class LLMResponseError(LLMError):
    """The server returned an error or an invalid response."""

    code = "llm_response_error"


class LlamaCppClient:
    """Client for OpenAI-compatible chat and embedding endpoints."""

    def __init__(
        self,
        base_url: str,
        *,
        connect_timeout: float = 5.0,
        request_timeout: float = 600.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(request_timeout, connect=connect_timeout)
        self._health_timeout = httpx.Timeout(min(5.0, request_timeout), connect=connect_timeout)

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
                base_url=self.base_url,
                timeout=timeout or self._timeout,
            ) as client:
                response = client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise LLMUnavailable(
                f"Could not reach llama.cpp server at {self.base_url}. "
                "Start llama-server and try again."
            ) from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            raise LLMTimeout(
                f"llama.cpp server at {self.base_url} timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable(
                f"Could not talk to llama.cpp server at {self.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            self._raise_response(response, model=model)
        return response

    @staticmethod
    def _raise_response(response: httpx.Response, *, model: str | None) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        detail = ""
        if isinstance(payload, dict):
            error = payload.get("error")
            detail = str(error.get("message", error) if isinstance(error, dict) else error or "")

        if response.status_code == 404 and model:
            raise ModelNotFound(
                f"Model '{model}' is not loaded by the llama.cpp server.",
                status_code=response.status_code,
                detail=detail,
            )
        if response.status_code >= 500:
            raise LLMUnavailable(
                f"llama.cpp server at {response.request.url} reported "
                f"{detail or response.status_code}.",
                status_code=response.status_code,
                detail=detail,
            )
        raise LLMResponseError(
            detail or f"llama.cpp server returned HTTP {response.status_code}.",
            status_code=response.status_code,
            detail=detail,
        )

    def health(self) -> None:
        """Raise a typed error unless the server is ready to accept requests."""
        self._request("GET", "/health", timeout=self._health_timeout)

    @staticmethod
    def _json_payload(response: httpx.Response, operation: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise LLMResponseError(
                f"llama.cpp returned invalid JSON for {operation}."
            ) from exc
        if not isinstance(payload, dict):
            raise LLMResponseError(f"llama.cpp returned an invalid {operation} response.")
        return payload

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        """Embed a batch via the OpenAI-compatible embeddings endpoint."""
        if not texts:
            return []
        response = self._request(
            "POST",
            "/v1/embeddings",
            model=model,
            json={"model": model, "input": texts, "encoding_format": "float"},
        )
        payload = self._json_payload(response, "embeddings")
        items = payload.get("data")
        if not isinstance(items, list) or len(items) != len(texts):
            raise LLMResponseError(
                f"llama.cpp returned {len(items) if isinstance(items, list) else 0} "
                f"embeddings for {len(texts)} inputs.",
                detail=str(payload)[:500],
            )

        ordered: list[list[float] | None] = [None] * len(texts)
        for item in items:
            if not isinstance(item, dict):
                raise LLMResponseError("llama.cpp returned an invalid embedding item.")
            index = item.get("index")
            vector = item.get("embedding")
            if (
                not isinstance(index, int)
                or not 0 <= index < len(texts)
                or not isinstance(vector, list)
                or not all(isinstance(value, (int, float)) for value in vector)
            ):
                raise LLMResponseError("llama.cpp returned an invalid embedding vector.")
            ordered[index] = [float(value) for value in vector]

        if any(vector is None for vector in ordered):
            raise LLMResponseError("llama.cpp omitted one or more embedding vectors.")
        return [vector for vector in ordered if vector is not None]

    @staticmethod
    def _chat_payload(
        model: str,
        messages: list[dict[str, Any]],
        options: dict[str, Any] | None,
        think: bool | None,
        *,
        stream: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if options and "temperature" in options:
            payload["temperature"] = options["temperature"]
        if think is not None:
            payload["chat_template_kwargs"] = {"enable_thinking": think}
        return payload

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> dict[str, Any]:
        """Run a non-streaming completion in the pipeline's normalized shape."""
        response = self._request(
            "POST",
            "/v1/chat/completions",
            model=model,
            json=self._chat_payload(model, messages, options, think, stream=False),
        )
        payload = self._json_payload(response, "chat")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise LLMResponseError("llama.cpp returned an unexpected chat response.")
        message = choices[0].get("message") or {}
        if not isinstance(message, dict):
            raise LLMResponseError("llama.cpp returned an invalid chat message.")
        return {
            "message": {
                "content": message.get("content") or "",
                "thinking": message.get("reasoning_content") or "",
            }
        }

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield normalized content/reasoning events from an OpenAI SSE stream."""
        payload = self._chat_payload(model, messages, options, think, stream=True)
        try:
            with httpx.Client(base_url=self.base_url, timeout=self._timeout) as client:
                with client.stream(
                    "POST", "/v1/chat/completions", json=payload
                ) as response:
                    if response.status_code >= 400:
                        response.read()
                        self._raise_response(response, model=model)
                    for line in response.iter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            yield {"done": True}
                            return
                        try:
                            event = json.loads(data)
                        except json.JSONDecodeError as exc:
                            raise LLMResponseError(
                                "llama.cpp returned malformed streaming data.",
                                detail=data[:500],
                            ) from exc
                        if not isinstance(event, dict):
                            raise LLMResponseError(
                                "llama.cpp returned an invalid streaming event."
                            )
                        if event.get("error"):
                            error = event["error"]
                            raise LLMResponseError(str(error))
                        choices = event.get("choices") or []
                        if not choices:
                            continue
                        choice = choices[0]
                        if not isinstance(choice, dict):
                            raise LLMResponseError(
                                "llama.cpp returned an invalid chat choice."
                            )
                        delta = choice.get("delta") or {}
                        if not isinstance(delta, dict):
                            raise LLMResponseError(
                                "llama.cpp returned an invalid chat delta."
                            )
                        message: dict[str, str] = {}
                        content = delta.get("content")
                        reasoning = delta.get("reasoning_content")
                        if content:
                            message["content"] = content
                        if reasoning:
                            message["thinking"] = reasoning
                        if message:
                            yield {"message": message}
                        if choice.get("finish_reason") is not None:
                            yield {"done": True}
                            return
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            raise LLMUnavailable(
                f"Could not reach llama.cpp server at {self.base_url}. "
                "Start llama-server and try again."
            ) from exc
        except (httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
            raise LLMTimeout(
                f"llama.cpp server at {self.base_url} stopped responding."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable(
                f"Connection to llama.cpp server at {self.base_url} failed: {exc}"
            ) from exc

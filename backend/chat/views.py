"""Conversation endpoints and the SSE answer stream."""

from __future__ import annotations

import json
import logging

from django.http import StreamingHttpResponse
from rag.ollama_client import (
    ModelNotFound,
    OllamaError,
    OllamaResponseError,
    OllamaUnavailable,
)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Conversation, Message
from .serializers import AskSerializer, ConversationSerializer, MessageSerializer

logger = logging.getLogger(__name__)


def sse(event: str, data) -> str:
    """One Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def error_status(exc: OllamaError) -> int:
    if isinstance(exc, OllamaUnavailable):
        return 503
    if isinstance(exc, ModelNotFound):
        return 409
    if isinstance(exc, OllamaResponseError):
        return 502
    return 502


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Conversation.objects.select_related("knowledge_base")
        kb_id = self.request.query_params.get("knowledge_base")
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        return queryset

    @action(detail=True, methods=["post"])
    def messages(self, request, pk=None):
        """Ask a question. Streams by default; send ``stream: false`` for JSON."""
        conversation = self.get_object()
        ask = AskSerializer(data=request.data)
        ask.is_valid(raise_exception=True)
        data = ask.validated_data
        question = data["question"]

        history = services.conversation_history(conversation)
        services.save_message(conversation, Message.Role.USER, question)
        if not conversation.title:
            conversation.title = services.title_from(question)
            conversation.save(update_fields=["title", "updated_at"])

        options = services.pipeline_options(conversation, history, data)
        if not data.get("stream", True):
            return self._answer_json(conversation, question, options)
        return self._answer_stream(conversation, question, options)

    def _answer_json(
        self,
        conversation: Conversation,
        question: str,
        options: dict,
    ) -> Response:
        parts: list[str] = []
        sources: list[dict] = []
        try:
            for event in services.stream_answer(conversation, question, options=options):
                if event.type == "sources":
                    sources = services.sources_payload(event.sources)
                elif event.type == "delta" and not event.thinking:
                    parts.append(event.text)
        except OllamaError as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=error_status(exc),
            )

        message = services.save_message(
            conversation,
            Message.Role.ASSISTANT,
            "".join(parts).strip(),
            sources=sources,
            model_used=conversation.chat_model,
        )
        return Response(
            {
                "message": MessageSerializer(message).data,
                "sources": sources,
            }
        )

    def _answer_stream(
        self,
        conversation: Conversation,
        question: str,
        options: dict,
    ) -> StreamingHttpResponse:
        def generate():
            parts: list[str] = []
            sources: list[dict] = []
            saved = False

            def persist() -> Message | None:
                nonlocal saved
                if saved:
                    return None
                text = "".join(parts).strip()
                if not text:
                    return None
                saved = True
                return services.save_message(
                    conversation,
                    Message.Role.ASSISTANT,
                    text,
                    sources=sources,
                    model_used=conversation.chat_model,
                )

            try:
                for event in services.stream_answer(conversation, question, options=options):
                    if event.type == "sources":
                        sources = services.sources_payload(event.sources)
                        yield sse("sources", sources)
                    elif event.type == "delta" and not event.thinking:
                        parts.append(event.text)
                        yield sse("token", {"text": event.text})
                    elif event.type == "done":
                        message = persist()
                        yield sse("done", {"message_id": getattr(message, "id", None)})
            except OllamaError as exc:
                persist()
                yield sse("error", {"detail": str(exc), "code": exc.code})
            except Exception:  # noqa: BLE001 - always tell the client something
                logger.exception("Answer failed for conversation %s", conversation.id)
                persist()
                yield sse(
                    "error",
                    {
                        "detail": "Something went wrong while answering.",
                        "code": "internal_error",
                    },
                )
            finally:
                persist()

        response = StreamingHttpResponse(generate(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

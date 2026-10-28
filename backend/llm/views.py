"""Ollama health and model discovery endpoints."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rag.ollama_client import OllamaError, OllamaUnavailable
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import AppSettings
from .serializers import (
    AppSettingsSerializer,
    ErrorSerializer,
    HealthResponseSerializer,
    ModelsResponseSerializer,
)


@extend_schema(
    tags=["system"],
    summary="Backend and Ollama health",
    responses={200: HealthResponseSerializer},
)
@api_view(["GET"])
def health(request: Request) -> Response:
    """Always returns 200; ``status`` is ``degraded`` if Ollama or the DB is down."""
    return Response(services.get_health())


@extend_schema(
    tags=["system"],
    summary="List installed Ollama models",
    parameters=[
        OpenApiParameter(
            name="refresh",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Bypass the 30 second cache.",
        )
    ],
    responses={200: ModelsResponseSerializer, 502: ErrorSerializer, 503: ErrorSerializer},
)
@api_view(["GET"])
def models(request: Request) -> Response:
    """Split installed models into chat and embedding models."""
    refresh = request.query_params.get("refresh", "").lower() in {"1", "true", "yes"}
    try:
        discovered, cloud_hidden, base_url = services.visible_models(force=refresh)
    except OllamaUnavailable as exc:
        return Response(
            {"detail": str(exc), "code": exc.code},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except OllamaError as exc:
        return Response(
            {"detail": str(exc), "code": exc.code},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response(
        {
            "chat": [model.as_dict() for model in discovered if model.kind == "chat"],
            "embedding": [
                model.as_dict() for model in discovered if model.kind == "embedding"
            ],
            "cloud_hidden": cloud_hidden,
            "base_url": base_url,
        }
    )


@extend_schema(
    tags=["system"],
    summary="Read or change app defaults",
    request=AppSettingsSerializer,
    responses={200: AppSettingsSerializer},
)
@api_view(["GET", "PATCH"])
def app_settings(request: Request) -> Response:
    """GET returns the defaults; PATCH updates whichever fields you send."""
    obj = AppSettings.load()
    if request.method == "GET":
        return Response(AppSettingsSerializer(obj).data)

    serializer = AppSettingsSerializer(obj, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

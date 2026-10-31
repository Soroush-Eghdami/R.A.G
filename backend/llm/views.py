"""llama.cpp health and configured model endpoints."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import AppSettings
from .serializers import (
    AppSettingsSerializer,
    HealthResponseSerializer,
    ModelsResponseSerializer,
)


@extend_schema(
    tags=["system"],
    summary="Backend and llama.cpp server health",
    responses={200: HealthResponseSerializer},
)
@api_view(["GET"])
def health(request: Request) -> Response:
    """Always returns 200; status is degraded if a model server or DB is down."""
    return Response(services.get_health())


@extend_schema(
    tags=["system"],
    summary="List configured llama.cpp models",
    parameters=[
        OpenApiParameter(
            name="refresh",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Accepted for compatibility; configured aliases are returned.",
        )
    ],
    responses={200: ModelsResponseSerializer},
)
@api_view(["GET"])
def models(request: Request) -> Response:
    """Return configured chat and embedding aliases."""
    del request
    discovered, _, _ = services.visible_models()
    return Response(
        {
            "chat": [model.as_dict() for model in discovered if model.kind == "chat"],
            "embedding": [
                model.as_dict() for model in discovered if model.kind == "embedding"
            ],
            "chat_base_url": services.build_chat_client().base_url,
            "embedding_base_url": services.build_embedding_client().base_url,
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

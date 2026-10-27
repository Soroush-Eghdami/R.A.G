"""Knowledge base and document endpoints."""

from __future__ import annotations

import hashlib
from pathlib import Path

from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from . import services
from .models import Document, KnowledgeBase
from .serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
    KnowledgeBaseSerializer,
)
from .tasks import enqueue_ingestion


def sha256_of(upload) -> str:
    """Hash an upload, then rewind it so it can be saved."""
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return digest.hexdigest()


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer

    def perform_destroy(self, instance: KnowledgeBase) -> None:
        services.build_store().drop(str(instance.id))
        # Cascade deletes skip Model.delete(), so remove files here.
        for document in instance.documents.all():
            if document.file:
                document.file.delete(save=False)
        instance.delete()


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        queryset = Document.objects.select_related("knowledge_base")
        kb_id = self.request.query_params.get("knowledge_base")
        if kb_id:
            queryset = queryset.filter(knowledge_base_id=kb_id)
        return queryset

    def create(self, request, *args, **kwargs):
        upload = DocumentUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        knowledge_base = upload.validated_data["knowledge_base"]
        file = upload.validated_data["file"]

        digest = sha256_of(file)
        duplicate = Document.objects.filter(
            knowledge_base=knowledge_base,
            sha256=digest,
        ).first()
        if duplicate is not None:
            return Response(
                {
                    "detail": "This file is already in the knowledge base.",
                    "document_id": str(duplicate.id),
                },
                status=status.HTTP_409_CONFLICT,
            )

        document = Document.objects.create(
            knowledge_base=knowledge_base,
            file=file,
            original_name=file.name,
            file_type=Path(file.name).suffix.lower().lstrip("."),
            size_bytes=file.size,
            sha256=digest,
        )
        enqueue_ingestion(str(document.id))
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance: Document) -> None:
        services.build_store().delete_document(
            str(instance.knowledge_base_id),
            str(instance.id),
        )
        instance.delete()

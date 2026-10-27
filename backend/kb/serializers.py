"""Serializers for knowledge bases and documents."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from rag.loaders import SUPPORTED_SUFFIXES
from rest_framework import serializers

from .models import Document, KnowledgeBase


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    is_locked = serializers.BooleanField(read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeBase
        fields = [
            "id",
            "name",
            "description",
            "embedding_model",
            "chunk_size",
            "chunk_overlap",
            "is_locked",
            "document_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_document_count(self, obj: KnowledgeBase) -> int:
        return obj.documents.count()

    def validate_embedding_model(self, value: str) -> str:
        instance = self.instance
        if (
            instance is not None
            and instance.is_locked
            and value != instance.embedding_model
        ):
            raise serializers.ValidationError(
                "The embedding model is locked once documents are indexed. "
                "Create a new knowledge base to use a different one."
            )
        return value

    def validate(self, attrs):
        chunk_size = attrs.get("chunk_size")
        chunk_overlap = attrs.get("chunk_overlap")
        if chunk_size is None:
            chunk_size = (
                self.instance.chunk_size if self.instance else settings.DEFAULT_CHUNK_SIZE
            )
        if chunk_overlap is None:
            chunk_overlap = (
                self.instance.chunk_overlap
                if self.instance
                else settings.DEFAULT_CHUNK_OVERLAP
            )
        if chunk_overlap >= chunk_size:
            raise serializers.ValidationError(
                {"chunk_overlap": "Overlap must be smaller than the chunk size."}
            )
        return attrs


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "knowledge_base",
            "original_name",
            "file_type",
            "size_bytes",
            "status",
            "error",
            "page_count",
            "chunk_count",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "error",
            "page_count",
            "chunk_count",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj: Document):
        if not obj.file:
            return None
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)


class DocumentUploadSerializer(serializers.Serializer):
    knowledge_base = serializers.PrimaryKeyRelatedField(
        queryset=KnowledgeBase.objects.all()
    )
    file = serializers.FileField()

    def validate_file(self, value):
        suffix = Path(value.name).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise serializers.ValidationError(
                f"Unsupported file type '{suffix}'. "
                f"Supported: {', '.join(SUPPORTED_SUFFIXES)}."
            )
        limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if value.size > limit:
            raise serializers.ValidationError(
                f"File is larger than {settings.MAX_UPLOAD_SIZE_MB} MB."
            )
        return value

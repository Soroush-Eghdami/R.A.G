"""Knowledge bases and their documents."""

from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def _chunk_size_default() -> int:
    return settings.DEFAULT_CHUNK_SIZE


def _chunk_overlap_default() -> int:
    return settings.DEFAULT_CHUNK_OVERLAP


def document_upload_path(instance: "Document", filename: str) -> str:
    """Keep files apart: media/kb/<kb id>/<document id><ext>."""
    suffix = Path(filename).suffix.lower()
    return f"kb/{instance.knowledge_base_id}/{instance.id}{suffix}"


class KnowledgeBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    # Changing this after upload requires a reindex.
    embedding_model = models.CharField(max_length=200)
    chunk_size = models.PositiveIntegerField(default=_chunk_size_default)
    chunk_overlap = models.PositiveIntegerField(default=_chunk_overlap_default)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_locked(self) -> bool:
        return self.documents.filter(status=Document.Status.READY).exists()


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        related_name="documents",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=document_upload_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20)
    size_bytes = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error = models.TextField(blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    chunk_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["knowledge_base", "sha256"],
                name="unique_document_per_kb",
            )
        ]

    def __str__(self) -> str:
        return self.original_name

    def delete(self, *args, **kwargs):
        """Remove the stored file with the row."""
        file = self.file
        super().delete(*args, **kwargs)
        if file:
            file.delete(save=False)

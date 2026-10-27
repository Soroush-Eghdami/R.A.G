"""Background ingestion: one worker thread, no Celery."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections

from . import services
from .models import Document

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ingest")


def enqueue_ingestion(document_id: str) -> None:
    """Queue a document and return immediately."""
    _executor.submit(run_ingestion, str(document_id))


def run_ingestion(document_id: str) -> None:
    """Parse, embed and store one document. Safe to call directly in tests."""
    close_old_connections()
    try:
        try:
            document = Document.objects.select_related("knowledge_base").get(
                pk=document_id
            )
        except Document.DoesNotExist:
            return

        document.status = Document.Status.PROCESSING
        document.error = ""
        document.save(update_fields=["status", "error", "updated_at"])

        try:
            result = services.ingest(document)
        except Exception as exc:  # noqa: BLE001 - status must always settle
            logger.exception("Ingestion failed for %s", document_id)
            document.status = Document.Status.FAILED
            document.error = str(exc)[:2000]
            document.save(update_fields=["status", "error", "updated_at"])
            return

        document.status = Document.Status.READY
        document.page_count = result.pages
        document.chunk_count = result.chunks
        document.save(
            update_fields=["status", "page_count", "chunk_count", "updated_at"]
        )
    finally:
        close_old_connections()


def recover_stuck_documents() -> int:
    """Anything still 'processing' died with the previous process."""
    return Document.objects.filter(status=Document.Status.PROCESSING).update(
        status=Document.Status.FAILED,
        error="Server restarted before ingestion finished.",
    )

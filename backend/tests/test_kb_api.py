"""Knowledge base and upload API tests."""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from kb import services as kb_services
from kb.models import Document, KnowledgeBase
from kb.tasks import recover_stuck_documents, run_ingestion
from rag.vectorstore import VectorStore

pytestmark = pytest.mark.django_db


class FakeEmbedder:
    model = "fake-embed"

    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.CHROMA_DIR = tmp_path / "chroma"


@pytest.fixture
def kb(db):
    return KnowledgeBase.objects.create(name="Docs", embedding_model="fake-embed")


@pytest.fixture
def store(settings, monkeypatch):
    store = VectorStore(settings.CHROMA_DIR)
    monkeypatch.setattr(kb_services, "build_store", lambda: store)
    monkeypatch.setattr(kb_services, "build_embedder", lambda model: FakeEmbedder())
    return store


def upload(client, kb, name="notes.txt", content=b"Alpha is the first letter."):
    return client.post(
        "/api/documents/",
        {
            "knowledge_base": str(kb.id),
            "file": SimpleUploadedFile(name, content),
        },
        format="multipart",
    )


def test_create_knowledge_base(client):
    response = client.post(
        "/api/knowledge-bases/",
        {"name": "Research", "embedding_model": "nomic-embed-text:latest"},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["is_locked"] is False
    assert body["document_count"] == 0


def test_duplicate_name_is_rejected(client, kb):
    response = client.post(
        "/api/knowledge-bases/",
        {"name": kb.name, "embedding_model": "nomic-embed-text:latest"},
        format="json",
    )
    assert response.status_code == 400


def test_upload_returns_202_and_queues(client, kb, monkeypatch):
    queued = []
    monkeypatch.setattr("kb.views.enqueue_ingestion", lambda doc_id: queued.append(doc_id))

    response = upload(client, kb)
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["original_name"] == "notes.txt"
    assert queued == [body["id"]]


def test_ingestion_marks_document_ready(client, kb, store):
    document_id = upload(client, kb).json()["id"]
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    assert document.status == Document.Status.READY
    assert document.chunk_count >= 1
    assert store.count(str(kb.id)) == document.chunk_count


def test_failed_ingestion_is_recorded(client, kb, store, monkeypatch):
    document_id = upload(client, kb).json()["id"]

    def boom(document):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(kb_services, "ingest", boom)
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    assert document.status == Document.Status.FAILED
    assert "model exploded" in document.error


def test_duplicate_file_is_rejected(client, kb):
    assert upload(client, kb).status_code == 202
    response = upload(client, kb)
    assert response.status_code == 409
    assert "already in the knowledge base" in response.json()["detail"]


def test_unsupported_extension_is_rejected(client, kb):
    response = upload(client, kb, name="data.zip", content=b"PK\x03\x04")
    assert response.status_code == 400


def test_oversized_file_is_rejected(client, kb, settings):
    settings.MAX_UPLOAD_SIZE_MB = 0
    response = upload(client, kb, content=b"x" * 2048)
    assert response.status_code == 400


def test_embedding_model_locks_after_indexing(client, kb, store):
    document_id = upload(client, kb).json()["id"]
    run_ingestion(document_id)

    url = f"/api/knowledge-bases/{kb.id}/"
    locked = client.patch(url, {"embedding_model": "other-model"}, format="json")
    assert locked.status_code == 400

    same = client.patch(url, {"embedding_model": "fake-embed"}, format="json")
    assert same.status_code == 200


def test_embedding_model_can_change_before_indexing(client, kb):
    response = client.patch(
        f"/api/knowledge-bases/{kb.id}/",
        {"embedding_model": "other-model"},
        format="json",
    )
    assert response.status_code == 200


def test_delete_document_removes_vectors_and_file(client, kb, store):
    document_id = upload(client, kb).json()["id"]
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    path = document.file.path
    assert store.count(str(kb.id)) == 1

    assert client.delete(f"/api/documents/{document_id}/").status_code == 204
    assert store.count(str(kb.id)) == 0
    assert not (document.file.storage.exists(path))


def test_delete_knowledge_base_drops_collection(client, kb, store):
    document_id = upload(client, kb).json()["id"]
    run_ingestion(document_id)

    assert client.delete(f"/api/knowledge-bases/{kb.id}/").status_code == 204
    assert store.count(str(kb.id)) == 0
    assert not Document.objects.filter(pk=document_id).exists()


def test_documents_can_be_filtered_by_kb(client, kb):
    other = KnowledgeBase.objects.create(name="Other", embedding_model="fake-embed")
    upload(client, kb)
    upload(client, other, name="other.txt")

    response = client.get(f"/api/documents/?knowledge_base={kb.id}")
    assert response.status_code == 200
    names = [item["original_name"] for item in response.json()]
    assert names == ["notes.txt"]


def test_recovery_marks_stuck_documents_failed(db):
    kb = KnowledgeBase.objects.create(name="Stuck", embedding_model="fake-embed")
    document = Document.objects.create(
        knowledge_base=kb,
        original_name="half.txt",
        file_type="txt",
        sha256="a" * 64,
        status=Document.Status.PROCESSING,
    )
    assert recover_stuck_documents() == 1
    document.refresh_from_db()
    assert document.status == Document.Status.FAILED
    assert "restarted" in document.error


def test_empty_pdf_marks_failed(client, kb, store, monkeypatch):
    """PDF with no extractable text gets friendly failure."""
    document_id = upload(client, kb, name="empty.pdf", content=b"%PDF-1.4\n%%EOF\n").json()["id"]

    from rag.loaders import EmptyDocument

    def empty_ingest(document):
        raise EmptyDocument("empty.pdf contains no text.")

    monkeypatch.setattr(kb_services, "ingest", empty_ingest)
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    assert document.status == Document.Status.FAILED
    assert document.error


def test_scanned_pdf_marks_failed(client, kb, store, monkeypatch):
    """Scanned PDF with no text gets friendly failure."""
    document_id = upload(
        client, kb, name="scan.pdf", content=b"%PDF-1.4 fake scan %%EOF\n"
    ).json()["id"]

    from rag.loaders import EmptyDocument

    def scan_ingest(document):
        raise EmptyDocument("scan.pdf contains no text.")

    monkeypatch.setattr(kb_services, "ingest", scan_ingest)
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    assert document.status == Document.Status.FAILED
    assert document.error


def test_llama_server_dies_mid_ingestion_marks_failed(client, kb, store, monkeypatch):
    """If llama.cpp becomes unavailable during ingestion, document is marked failed."""
    document_id = upload(client, kb).json()["id"]

    from rag.llama_cpp_client import LLMUnavailable

    def boom(document):
        raise LLMUnavailable("llama.cpp connection lost")

    monkeypatch.setattr(kb_services, "ingest", boom)
    run_ingestion(document_id)

    document = Document.objects.get(pk=document_id)
    assert document.status == Document.Status.FAILED
    assert document.error


def test_delete_kb_during_ingestion_cleans_up(client, kb, store, monkeypatch):
    """Deleting KB while ingestion is running cleans up vectors and marks docs failed."""
    document_id = upload(client, kb).json()["id"]
    document = Document.objects.get(pk=document_id)
    document.status = Document.Status.PROCESSING
    document.save()

    # Delete the KB.
    resp = client.delete(f"/api/knowledge-bases/{kb.id}/")
    assert resp.status_code == 204

    # The KB and document are gone.
    assert not KnowledgeBase.objects.filter(pk=kb.id).exists()
    assert not Document.objects.filter(pk=document_id).exists()
    # The vector collection is gone.
    assert store.count(str(kb.id)) == 0

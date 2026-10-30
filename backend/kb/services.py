"""Build the RAG pieces from Django settings."""

from __future__ import annotations

from django.conf import settings
from llm.services import build_embedding_client
from rag.embedder import LlamaCppEmbedder
from rag.pipeline import IngestResult, KnowledgeBaseConfig, ingest_document
from rag.vectorstore import VectorStore

from .models import Document, KnowledgeBase


def build_store() -> VectorStore:
    return VectorStore(settings.CHROMA_DIR)


def build_embedder(model: str) -> LlamaCppEmbedder:
    return LlamaCppEmbedder(build_embedding_client(), model)


def config_for(kb: KnowledgeBase) -> KnowledgeBaseConfig:
    return KnowledgeBaseConfig(
        id=str(kb.id),
        embedding_model=kb.embedding_model,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        top_k=settings.DEFAULT_TOP_K,
    )


def ingest(document: Document) -> IngestResult:
    """Index one uploaded document."""
    kb = document.knowledge_base
    return ingest_document(
        document.file.path,
        config_for(kb),
        store=build_store(),
        embedder=build_embedder(kb.embedding_model),
        document_id=str(document.id),
        document_name=document.original_name,
    )

"""ChromaDB wrapper: one collection per knowledge base."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings

from .chunking import Chunk

COLLECTION_PREFIX = "kb"
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]")


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A vector match with enough info to cite it."""

    id: str
    document_id: str
    document_name: str
    text: str
    chunk_index: int
    distance: float
    page: int | None = None
    heading: str | None = None


class VectorStore:
    """Persistent Chroma client, cosine space."""

    def __init__(
        self,
        path: str | Path,
        *,
        collection_prefix: str = COLLECTION_PREFIX,
    ) -> None:
        self._path = Path(path)
        self._prefix = collection_prefix
        self._client: chromadb.ClientAPI | None = None
        self._collections: dict[str, Any] = {}
        self._lock = threading.Lock()

    def _get_client(self) -> chromadb.ClientAPI:
        with self._lock:
            if self._client is None:
                self._path.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self._path),
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=False,
                    ),
                )
            return self._client

    def collection_name(self, kb_id: str) -> str:
        safe = _SAFE_NAME.sub("_", str(kb_id)).strip("._-") or "default"
        return f"{self._prefix}_{safe}"

    def _collection(self, kb_id: str, *, create: bool) -> Any | None:
        name = self.collection_name(kb_id)
        with self._lock:
            cached = self._collections.get(name)
        if cached is not None:
            return cached

        client = self._get_client()
        if create:
            collection = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            try:
                collection = client.get_collection(name=name)
            except Exception:  # noqa: BLE001 - chroma raises several types
                return None
        with self._lock:
            self._collections[name] = collection
        return collection

    def add_chunks(
        self,
        kb_id: str,
        document_id: str,
        chunks: Sequence[Chunk],
        embeddings: Sequence[Sequence[float]],
        *,
        document_name: str = "",
    ) -> int:
        """Add or replace a document's chunks. Returns how many were stored."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"{len(chunks)} chunks but {len(embeddings)} embeddings were provided."
            )
        if not chunks:
            return 0

        collection = self._collection(kb_id, create=True)
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        for chunk in chunks:
            ids.append(f"{document_id}:{chunk.index}")
            documents.append(chunk.text)
            metadata: dict[str, Any] = {
                "document_id": document_id,
                "chunk_index": chunk.index,
            }
            if document_name:
                metadata["document_name"] = document_name
            if chunk.page is not None:
                metadata["page"] = int(chunk.page)
            if chunk.heading:
                metadata["heading"] = chunk.heading
            metadatas.append(metadata)

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=[list(vector) for vector in embeddings],
            metadatas=metadatas,
        )
        return len(ids)

    def delete_document(self, kb_id: str, document_id: str) -> None:
        """Remove one document's chunks."""
        collection = self._collection(kb_id, create=False)
        if collection is None:
            return
        collection.delete(where={"document_id": document_id})

    def drop(self, kb_id: str) -> None:
        """Delete a whole knowledge base collection."""
        name = self.collection_name(kb_id)
        client = self._get_client()
        with self._lock:
            self._collections.pop(name, None)
        try:
            client.delete_collection(name=name)
        except Exception:  # noqa: BLE001 - already gone is fine
            return

    def count(self, kb_id: str) -> int:
        collection = self._collection(kb_id, create=False)
        return 0 if collection is None else int(collection.count())

    def query(
        self,
        kb_id: str,
        embedding: Sequence[float],
        *,
        top_k: int = 4,
    ) -> list[RetrievedChunk]:
        """Nearest chunks, closest first."""
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        collection = self._collection(kb_id, create=False)
        if collection is None or collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[list(embedding)],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]

        matches: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            metadata = metadata or {}
            page = metadata.get("page")
            matches.append(
                RetrievedChunk(
                    id=str(chunk_id),
                    document_id=str(metadata.get("document_id", "")),
                    document_name=str(metadata.get("document_name", "")),
                    text=text or "",
                    chunk_index=int(metadata.get("chunk_index", 0) or 0),
                    distance=float(distance),
                    page=int(page) if page is not None else None,
                    heading=metadata.get("heading"),
                )
            )
        return matches

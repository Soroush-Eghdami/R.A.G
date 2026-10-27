"""Vector store tests against a real temporary Chroma."""

from __future__ import annotations

import pytest
from rag.chunking import Chunk
from rag.vectorstore import VectorStore


@pytest.fixture
def store(tmp_path):
    return VectorStore(tmp_path / "chroma")


def _chunks(texts):
    return [Chunk(text=text, index=index) for index, text in enumerate(texts)]


def test_add_and_query(store):
    chunks = _chunks(["alpha text", "beta text"])
    store.add_chunks("kb1", "doc1", chunks, [[1.0, 0.0], [0.0, 1.0]], document_name="a.txt")

    matches = store.query("kb1", [1.0, 0.0], top_k=2)
    assert matches[0].text == "alpha text"
    assert matches[0].document_id == "doc1"
    assert matches[0].document_name == "a.txt"
    assert matches[0].distance < matches[1].distance


def test_metadata_is_preserved(store):
    chunk = Chunk(text="paged", index=0, page=4, heading="Intro")
    store.add_chunks("kb1", "doc1", [chunk], [[1.0, 0.0]])

    match = store.query("kb1", [1.0, 0.0], top_k=1)[0]
    assert match.page == 4
    assert match.heading == "Intro"
    assert match.chunk_index == 0


def test_reingest_replaces_instead_of_duplicating(store):
    chunks = _chunks(["first version"])
    store.add_chunks("kb1", "doc1", chunks, [[1.0, 0.0]])
    store.add_chunks("kb1", "doc1", chunks, [[1.0, 0.0]])
    assert store.count("kb1") == 1


def test_delete_document_only_removes_that_document(store):
    store.add_chunks("kb1", "doc1", _chunks(["a"]), [[1.0, 0.0]])
    store.add_chunks("kb1", "doc2", _chunks(["b"]), [[0.0, 1.0]])

    store.delete_document("kb1", "doc1")
    assert store.count("kb1") == 1
    assert store.query("kb1", [1.0, 0.0], top_k=5)[0].document_id == "doc2"


def test_drop_removes_collection(store):
    store.add_chunks("kb1", "doc1", _chunks(["a"]), [[1.0, 0.0]])
    store.drop("kb1")
    assert store.count("kb1") == 0


def test_query_unknown_kb_is_empty(store):
    assert store.query("missing", [1.0, 0.0]) == []


def test_mismatched_embeddings_raise(store):
    with pytest.raises(ValueError):
        store.add_chunks("kb1", "doc1", _chunks(["a", "b"]), [[1.0, 0.0]])


def test_knowledge_bases_are_isolated(store):
    store.add_chunks("kb1", "doc1", _chunks(["alpha"]), [[1.0, 0.0]])
    store.add_chunks("kb2", "doc2", _chunks(["beta"]), [[0.0, 1.0]])
    assert store.query("kb1", [1.0, 0.0], top_k=5)[0].text == "alpha"
    assert store.query("kb2", [1.0, 0.0], top_k=5)[0].text == "beta"

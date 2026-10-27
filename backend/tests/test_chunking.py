"""Chunking tests."""

from __future__ import annotations

import pytest
from rag.chunking import ChunkConfig, chunk_blocks, chunk_text, split_text
from rag.loaders import TextBlock


def test_short_text_stays_whole():
    assert split_text("Short text.") == ["Short text."]


def test_long_text_splits_within_budget():
    text = ("This is a sentence that keeps going. " * 200).strip()
    config = ChunkConfig(chunk_size=500, chunk_overlap=80)
    pieces = split_text(text, config)
    assert len(pieces) > 1
    assert all(len(piece) <= 500 for piece in pieces)
    assert all(piece.endswith(".") for piece in pieces)


def test_chunks_overlap():
    text = ("Alpha beta gamma delta epsilon zeta eta theta. " * 40).strip()
    config = ChunkConfig(chunk_size=300, chunk_overlap=100)
    pieces = split_text(text, config)
    assert len(pieces) >= 2
    assert pieces[0][-40:] in pieces[1]


def test_no_break_characters_still_splits():
    text = "x" * 2000
    pieces = split_text(text, ChunkConfig(chunk_size=400, chunk_overlap=50))
    assert all(len(piece) <= 400 for piece in pieces)
    assert "".join(pieces).count("x") >= 2000


def test_small_tail_is_merged():
    text = "a" * 290 + ". " + "b" * 20
    pieces = split_text(text, ChunkConfig(chunk_size=300, chunk_overlap=50, min_chunk_chars=80))
    assert len(pieces) == 1
    assert pieces[0].endswith("b" * 20)


def test_blocks_keep_page_and_heading():
    blocks = [TextBlock(text="Some body text.", page=7, heading="Intro > Scope")]
    chunks = chunk_blocks(blocks)
    assert chunks[0].page == 7
    assert chunks[0].heading == "Intro > Scope"
    assert chunks[0].text.startswith("[Section: Intro > Scope]")


def test_chunk_indexes_are_sequential():
    chunks = chunk_text("Sentence one. Sentence two. Sentence three.")
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"chunk_size": 50},
        {"chunk_overlap": -1},
        {"chunk_size": 300, "chunk_overlap": 300},
        {"min_chunk_chars": -5},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        ChunkConfig(**kwargs)

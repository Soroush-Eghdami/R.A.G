"""Pipeline tests with a fake embedder and fake chat client."""

from __future__ import annotations

import pytest
from rag.ollama_client import OllamaUnavailable
from rag.pipeline import (
    KnowledgeBaseConfig,
    _tidy_rewrite,
    answer_stream,
    collect_answer,
    ingest_document,
    looks_like_follow_up,
)
from rag.prompts import NO_ANSWER
from rag.vectorstore import VectorStore


class FakeEmbedder:
    model = "fake-embed"

    def _vector(self, text: str) -> list[float]:
        lowered = text.lower()
        if "alpha" in lowered:
            return [1.0, 0.0, 0.0]
        if "beta" in lowered:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts):
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        return self._vector(text)


class FakeClient:
    def __init__(self, pieces=("The answer is ", "42."), rewrite="What is alpha?"):
        self.pieces = pieces
        self.rewrite = rewrite
        self.calls = []
        self.rewrites = []
        self.rewrite_error = None

    def chat(self, model, messages, *, options=None, think=None):
        self.rewrites.append({"model": model, "messages": messages, "options": options})
        if self.rewrite_error is not None:
            raise self.rewrite_error
        return {"message": {"content": self.rewrite}}

    def chat_stream(self, model, messages, *, options=None, think=None):
        self.calls.append(
            {"model": model, "messages": messages, "options": options, "think": think}
        )
        for piece in self.pieces:
            yield {"message": {"content": piece}}
        yield {"done": True}


@pytest.fixture
def kb():
    return KnowledgeBaseConfig(id="test", embedding_model="fake-embed", top_k=3)


@pytest.fixture
def store(tmp_path):
    return VectorStore(tmp_path / "chroma")


@pytest.fixture
def doc(tmp_path):
    path = tmp_path / "alpha.txt"
    path.write_text("Alpha is the first letter of the Greek alphabet.", encoding="utf-8")
    return path


def test_ingest_reports_what_it_stored(doc, kb, store):
    result = ingest_document(doc, kb, store=store, embedder=FakeEmbedder())
    assert result.chunks >= 1
    assert result.document_name == "alpha.txt"
    assert result.embedding_model == "fake-embed"
    assert store.count("test") == result.chunks


def test_answer_uses_retrieved_context(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    answer, sources = collect_answer(
        "What is alpha?",
        kb,
        chat_model="fake-chat",
        client=client,
        store=store,
        embedder=embedder,
    )

    assert answer == "The answer is 42."
    assert len(sources) == 1
    assert "Greek alphabet" in sources[0].text
    assert "Alpha is the first letter" in client.calls[0]["messages"][0]["content"]


def test_sources_event_comes_first(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)

    events = list(
        answer_stream(
            "What is alpha?",
            kb,
            chat_model="fake-chat",
            client=FakeClient(),
            store=store,
            embedder=embedder,
        )
    )
    assert events[0].type == "sources"
    assert events[-1].type == "done"
    assert events[-1].text == "The answer is 42."
    assert "".join(event.text for event in events if event.type == "delta") == (
        "The answer is 42."
    )


def test_off_topic_question_skips_the_model(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    answer, sources = collect_answer(
        "Tell me about beta.",
        kb,
        chat_model="fake-chat",
        client=client,
        store=store,
        embedder=embedder,
    )

    assert answer == NO_ANSWER
    assert sources == ()
    assert client.calls == []


def test_num_ctx_and_think_are_forwarded(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    collect_answer(
        "What is alpha?",
        kb,
        chat_model="fake-chat",
        client=client,
        store=store,
        embedder=embedder,
        num_ctx=4096,
        think=True,
    )

    call = client.calls[0]
    assert call["options"]["num_ctx"] == 4096
    assert call["think"] is True


def test_old_history_is_dropped_to_fit(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    history = [
        {"role": "user", "content": "old question " * 100},
        {"role": "assistant", "content": "old answer " * 100},
        {"role": "user", "content": "recent question"},
    ]
    collect_answer(
        "What is alpha?",
        kb,
        chat_model="fake-chat",
        client=client,
        store=store,
        embedder=embedder,
        history=history,
        num_ctx=1024,
    )

    messages = client.calls[0]["messages"]
    contents = [message["content"] for message in messages]
    assert "recent question" in contents
    assert not any("old question" in content for content in contents)


def test_blank_question_is_rejected(kb, store):
    with pytest.raises(ValueError):
        list(
            answer_stream(
                "   ",
                kb,
                chat_model="fake-chat",
                client=FakeClient(),
                store=store,
                embedder=FakeEmbedder(),
            )
        )


@pytest.mark.parametrize(
    "question",
    ["Why?", "And the email?", "Explain that more simply", "What about its limits?"],
)
def test_follow_ups_are_recognised(question):
    assert looks_like_follow_up(question) is True


@pytest.mark.parametrize(
    "question",
    [
        "What is the support email?",
        "How often does the nightly backup run?",
        "Which team launched Project Halcyon?",
    ],
)
def test_standalone_questions_are_not_rewritten(question):
    assert looks_like_follow_up(question) is False


def test_rewrite_emits_a_query_event_first(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient(rewrite="What are the limits of alpha?")

    events = list(
        answer_stream(
            "what about its limits?",
            kb,
            chat_model="fake-chat",
            client=client,
            store=store,
            embedder=embedder,
            history=[
                {"role": "user", "content": "Tell me about alpha."},
                {"role": "assistant", "content": "Alpha is the first letter."},
            ],
        )
    )

    assert events[0].type == "query"
    assert events[0].text == "What are the limits of alpha?"
    assert events[0].original == "what about its limits?"
    assert events[1].type == "sources"
    assert len(client.rewrites) == 1


def test_no_history_means_no_rewrite(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    events = list(
        answer_stream(
            "what about its limits?",
            kb,
            chat_model="fake-chat",
            client=client,
            store=store,
            embedder=embedder,
        )
    )

    assert events[0].type == "sources"
    assert client.rewrites == []


def test_failed_rewrite_still_answers(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()
    client.rewrite_error = OllamaUnavailable("Ollama went away")

    events = list(
        answer_stream(
            "what about its limits?",
            kb,
            chat_model="fake-chat",
            client=client,
            store=store,
            embedder=embedder,
            history=[{"role": "user", "content": "Tell me about alpha."}],
        )
    )

    assert [event.type for event in events][0] == "sources"
    assert events[-1].type == "done"


def test_rewrite_can_be_switched_off(doc, kb, store):
    embedder = FakeEmbedder()
    ingest_document(doc, kb, store=store, embedder=embedder)
    client = FakeClient()

    list(
        answer_stream(
            "what about its limits?",
            kb,
            chat_model="fake-chat",
            client=client,
            store=store,
            embedder=embedder,
            history=[{"role": "user", "content": "Tell me about alpha."}],
            rewrite_followups=False,
        )
    )

    assert client.rewrites == []


def test_messy_rewrite_reply_falls_back():
    assert _tidy_rewrite("Standalone query: alpha limits", "why?") == "alpha limits"
    assert _tidy_rewrite('"alpha limits"', "why?") == "alpha limits"
    assert _tidy_rewrite("", "why?") == "why?"
    assert _tidy_rewrite("x" * 400, "why?") == "why?"

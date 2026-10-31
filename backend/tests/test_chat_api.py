"""Chat API tests: JSON answers, SSE stream, search."""

from __future__ import annotations

import json

import pytest
from chat import services as chat_services
from chat.models import Conversation, Message
from kb import services as kb_services
from kb.models import KnowledgeBase
from llm.models import AppSettings
from rag.chunking import Chunk
from rag.llama_cpp_client import LLMUnavailable
from rag.vectorstore import VectorStore

pytestmark = pytest.mark.django_db


class FakeEmbedder:
    model = "fake-embed"

    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


class FakeClient:
    def __init__(self, pieces=("The answer ", "is 42."), rewrite="What are alpha's limits?"):
        self.pieces = pieces
        self.rewrite = rewrite
        self.calls = []
        self.rewrites = []

    def context_size(self):
        return 8192

    def chat(self, model, messages, *, options=None, think=None):
        self.rewrites.append({"model": model, "messages": messages})
        return {"message": {"content": self.rewrite}}

    def chat_stream(self, model, messages, *, options=None, think=None):
        self.calls.append(
            {"model": model, "messages": messages, "options": options, "think": think}
        )
        for piece in self.pieces:
            yield {"message": {"content": piece}}
        yield {"done": True}


class FailingClient(FakeClient):
    def chat_stream(self, model, messages, *, options=None, think=None):
        yield {"message": {"content": "half an ans"}}
        raise LLMUnavailable("llama.cpp server stopped responding.")


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.CHROMA_DIR = tmp_path / "chroma"


@pytest.fixture
def kb(db):
    return KnowledgeBase.objects.create(name="Chat KB", embedding_model="fake-embed")


@pytest.fixture
def settings_row(db):
    return AppSettings.objects.create(
        default_chat_model="fake-chat",
        top_k=3,
        num_ctx=4096,
        temperature=0.1,
    )


@pytest.fixture
def runtime(settings, kb, monkeypatch):
    store = VectorStore(settings.CHROMA_DIR)
    store.add_chunks(
        str(kb.id),
        "doc-1",
        [Chunk(text="Alpha is the first letter.", index=0)],
        [[1.0, 0.0, 0.0]],
        document_name="alpha.txt",
    )
    client = FakeClient()
    embedder = FakeEmbedder()
    monkeypatch.setattr(
        chat_services,
        "build_runtime",
        lambda knowledge_base: (client, store, embedder),
    )
    # Search builds its own store and embedder.
    monkeypatch.setattr(kb_services, "build_store", lambda: store)
    monkeypatch.setattr(kb_services, "build_embedder", lambda model: embedder)
    return client, store, embedder


def make_conversation(client, kb, **extra):
    payload = {"knowledge_base": str(kb.id), "chat_model": "fake-chat", **extra}
    return client.post("/api/conversations/", payload, format="json")


def test_conversation_uses_default_chat_model(client, kb, settings_row):
    response = client.post(
        "/api/conversations/",
        {"knowledge_base": str(kb.id)},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["chat_model"] == "fake-chat"


def test_conversation_uses_configured_chat_model_when_not_specified(client, kb):
    response = client.post(
        "/api/conversations/",
        {"knowledge_base": str(kb.id)},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["chat_model"] == "Qwen3.5-9B"


def test_json_answer_is_saved(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    response = client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"]["content"] == "The answer is 42."
    assert body["sources"][0]["document"] == "alpha.txt"
    assert body["sources"][0]["text"] == "Alpha is the first letter."

    conversation = Conversation.objects.get(pk=conversation_id)
    assert conversation.title == "What is alpha?"
    assert list(conversation.messages.values_list("role", flat=True)) == [
        Message.Role.USER,
        Message.Role.ASSISTANT,
    ]


def test_sse_stream_order_and_persistence(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    response = client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?"},
        format="json",
    )

    assert response["Content-Type"].startswith("text/event-stream")
    assert response["Cache-Control"] == "no-cache"

    raw = b"".join(response.streaming_content).decode("utf-8")
    events = [
        block.split("\n", 1)
        for block in raw.strip().split("\n\n")
    ]
    names = [line[0].removeprefix("event: ") for line in events]
    assert names == ["sources", "token", "token", "done"]

    tokens = "".join(
        json.loads(line[1].removeprefix("data: "))["text"]
        for name, line in zip(names, events)
        if name == "token"
    )
    assert tokens == "The answer is 42."

    saved = Message.objects.get(conversation_id=conversation_id, role=Message.Role.ASSISTANT)
    assert saved.content == "The answer is 42."
    assert saved.sources[0]["document"] == "alpha.txt"


def test_stream_error_event_keeps_partial_answer(client, kb, settings_row, runtime, monkeypatch):
    conversation_id = make_conversation(client, kb).json()["id"]
    failing = FailingClient()
    monkeypatch.setattr(
        chat_services,
        "build_runtime",
        lambda knowledge_base: (failing, runtime[1], runtime[2]),
    )

    response = client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?"},
        format="json",
    )
    raw = b"".join(response.streaming_content).decode("utf-8")
    assert "event: error" in raw
    assert "llm_unavailable" in raw

    saved = Message.objects.get(conversation_id=conversation_id, role=Message.Role.ASSISTANT)
    assert saved.content == "half an ans"


def test_history_is_sent_to_the_model(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    url = f"/api/conversations/{conversation_id}/messages/"
    client.post(url, {"question": "First?", "stream": False}, format="json")
    client.post(url, {"question": "Second?", "stream": False}, format="json")

    last_messages = runtime[0].calls[-1]["messages"]
    contents = [message["content"] for message in last_messages]
    assert any("First?" in content for content in contents)
    assert any("The answer is 42." in content for content in contents)


def test_options_come_from_settings_row(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False},
        format="json",
    )
    call = runtime[0].calls[-1]
    assert call["options"]["num_ctx"] == 4096
    assert call["options"]["temperature"] == 0.1
    assert call["options"]["max_tokens"] == 768
    assert call["think"] is False


def test_full_model_context_is_resolved_for_each_request(
    client, kb, settings_row, runtime
):
    settings_row.num_ctx = 0
    settings_row.save()
    runtime[0].context_size = lambda: 32768
    conversation_id = make_conversation(client, kb).json()["id"]

    client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False},
        format="json",
    )

    assert runtime[0].calls[-1]["options"]["num_ctx"] == 32768


def test_answer_length_is_forwarded_to_the_model(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    response = client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False, "answer_length": "detailed"},
        format="json",
    )

    assert response.status_code == 200
    call = runtime[0].calls[-1]
    assert call["options"]["max_tokens"] > 1536
    assert "Give a thorough answer" in call["messages"][0]["content"]


def test_search_returns_chunks_without_calling_the_model(client, kb, runtime):
    response = client.post(
        f"/api/knowledge-bases/{kb.id}/search/",
        {"question": "What is alpha?", "top_k": 2},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["document"] == "alpha.txt"
    assert "Alpha is the first letter." in body["results"][0]["text"]
    assert runtime[0].calls == []


def test_title_comes_from_the_first_question_only(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    url = f"/api/conversations/{conversation_id}/messages/"
    client.post(url, {"question": "What is alpha?", "stream": False}, format="json")
    client.post(url, {"question": "And beta?", "stream": False}, format="json")

    conversation = Conversation.objects.get(pk=conversation_id)
    assert conversation.title == "What is alpha?"


def test_chat_model_can_be_switched(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    response = client.patch(
        f"/api/conversations/{conversation_id}/",
        {"chat_model": "another-model"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["chat_model"] == "another-model"

    client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False},
        format="json",
    )
    assert runtime[0].calls[-1]["model"] == "another-model"


def test_follow_up_is_rewritten_before_search(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    url = f"/api/conversations/{conversation_id}/messages/"
    client.post(url, {"question": "What is the support email?", "stream": False}, format="json")

    response = client.post(url, {"question": "And what about it?", "stream": False}, format="json")

    assert response.status_code == 200
    assert response.json()["rewritten"] == "What are alpha's limits?"
    assert len(runtime[0].rewrites) == 1
    # The answer keeps the original question.
    assert runtime[0].calls[-1]["messages"][-1]["content"] == "And what about it?"


def test_plain_question_skips_the_rewrite(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    url = f"/api/conversations/{conversation_id}/messages/"
    client.post(url, {"question": "What is the support email?", "stream": False}, format="json")
    client.post(
        url,
        {"question": "How often does the nightly backup run?", "stream": False},
        format="json",
    )

    assert runtime[0].rewrites == []


def test_rewrite_shows_up_as_an_sse_event(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    url = f"/api/conversations/{conversation_id}/messages/"
    client.post(url, {"question": "What is the support email?", "stream": False}, format="json")

    response = client.post(url, {"question": "And what about it?"}, format="json")
    raw = b"".join(response.streaming_content).decode("utf-8")
    assert raw.startswith("event: query")
    assert "And what about it?" in raw


def test_delete_conversation_removes_messages(client, kb, settings_row, runtime):
    conversation_id = make_conversation(client, kb).json()["id"]
    client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "stream": False},
        format="json",
    )
    assert client.delete(f"/api/conversations/{conversation_id}/").status_code == 204
    assert not Message.objects.filter(conversation_id=conversation_id).exists()


class ThinkingClient(FakeClient):
    """Streams thinking pieces before the answer."""

    def chat_stream(self, model, messages, *, options=None, think=None):
        self.calls.append(
            {"model": model, "messages": messages, "options": options, "think": think}
        )
        yield {"message": {"thinking": "let me think"}}
        yield {"message": {"content": "The answer ", "thinking": " step 1"}}
        yield {"message": {"content": "is 42."}}
        yield {"done": True}


def test_thinking_events_appear_in_sse(client, kb, settings_row, runtime, monkeypatch):
    conversation_id = make_conversation(client, kb).json()["id"]
    thinking = ThinkingClient()
    monkeypatch.setattr(
        chat_services,
        "build_runtime",
        lambda knowledge_base: (thinking, runtime[1], runtime[2]),
    )

    response = client.post(
        f"/api/conversations/{conversation_id}/messages/",
        {"question": "What is alpha?", "think": True},
        format="json",
    )
    raw = b"".join(response.streaming_content).decode("utf-8")

    assert "event: thinking" in raw
    assert "let me think" in raw
    assert "event: token" in raw

    token_texts = []
    for block in raw.strip().split("\n\n"):
        lines = block.split("\n", 1)
        if lines[0] == "event: token":
            data = lines[1].removeprefix("data: ")
            token_texts.append(json.loads(data)["text"])
    assert "".join(token_texts) == "The answer is 42."

    saved = Message.objects.get(conversation_id=conversation_id, role=Message.Role.ASSISTANT)
    assert saved.content == "The answer is 42."

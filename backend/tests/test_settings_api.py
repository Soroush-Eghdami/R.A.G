"""App settings endpoint tests."""

from __future__ import annotations

import pytest
from llm.models import AppSettings

pytestmark = pytest.mark.django_db


def test_settings_return_defaults(client, settings):
    response = client.get("/api/settings/")
    assert response.status_code == 200
    body = response.json()
    assert body["top_k"] == settings.DEFAULT_TOP_K
    assert body["num_ctx"] == settings.DEFAULT_NUM_CTX
    assert body["ollama_base_url"] == settings.OLLAMA_BASE_URL


def test_settings_can_be_changed(client):
    response = client.patch(
        "/api/settings/",
        {"top_k": 6, "temperature": 0.4, "num_ctx": 4096},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["top_k"] == 6

    saved = AppSettings.load()
    assert saved.top_k == 6
    assert saved.temperature == 0.4
    assert saved.num_ctx == 4096


def test_base_url_is_read_only(client, settings):
    response = client.patch(
        "/api/settings/",
        {"ollama_base_url": "http://example.com:9999"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ollama_base_url"] == settings.OLLAMA_BASE_URL


@pytest.mark.parametrize(
    "payload",
    [{"top_k": 0}, {"top_k": 99}, {"temperature": 5}, {"num_ctx": 100}],
)
def test_bad_values_are_rejected(client, payload):
    response = client.patch("/api/settings/", payload, format="json")
    assert response.status_code == 400

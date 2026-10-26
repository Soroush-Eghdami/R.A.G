"""Phase 0 smoke tests: the project boots and the surfaces we rely on exist."""

import pytest
from django.conf import settings
from django.urls import reverse


def test_settings_are_env_driven():
    assert settings.OLLAMA_BASE_URL.startswith("http")
    assert settings.DATA_DIR.exists()
    assert settings.CHROMA_DIR.exists()
    assert settings.MEDIA_ROOT.exists()


def test_admin_login_is_available(client):
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200


def test_openapi_schema_is_available(client):
    response = client.get("/api/schema/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_database_is_migrated(db):
    from django.contrib.auth import get_user_model

    assert get_user_model().objects.count() == 0

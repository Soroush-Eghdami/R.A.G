import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(autouse=True)
def _no_startup_recovery(settings):
    settings.STARTUP_RECOVERY = False

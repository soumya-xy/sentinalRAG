from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.main import app
from app.services.store import store


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("MOCK_PROCESSING_SECONDS", "0")
    reset_settings_cache()
    store.clear()
    with TestClient(app) as test_client:
        yield test_client
    store.clear()
    reset_settings_cache()

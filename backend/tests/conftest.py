from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.main import app
from app.services.store import configure_store, store
from tests.fakes import skip_ingest_for_tests


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    reset_settings_cache()
    configure_store()
    store.clear()
    store.seed_demo_user()
    monkeypatch.setattr("app.api.videos.enqueue_ingest", skip_ingest_for_tests)
    with TestClient(app) as test_client:
        yield test_client
    store.clear()
    reset_settings_cache()

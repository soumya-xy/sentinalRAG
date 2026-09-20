import json
import logging

from fastapi.testclient import TestClient

from app.core.context import bind_log_context
from app.core.logging import JsonFormatter, configure_logging
from app.middleware.request_context import video_id_from_path
from tests.fakes import complete_ingest_for_tests, fake_mp4_bytes


def _auth(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"email": "demo@sentinelrag.dev", "password": "demo1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_log_records_include_bound_ids(caplog) -> None:
    configure_logging()
    logger = logging.getLogger("sentinelrag.test")
    with caplog.at_level(logging.INFO, logger="sentinelrag.test"):
        with bind_log_context(request_id="req_abc", video_id="vid_1", query_id="qry_9"):
            logger.info("hello lifecycle")
    record = caplog.records[-1]
    assert record.video_id == "vid_1"
    assert record.query_id == "qry_9"
    assert record.request_id == "req_abc"


def test_json_formatter_emits_filterable_fields() -> None:
    record = logging.LogRecord(
        name="sentinelrag.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="pipeline stage done",
        args=(),
        exc_info=None,
    )
    record.video_id = "vid_1"
    record.query_id = "-"
    record.request_id = "req_abc"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["video_id"] == "vid_1"
    assert payload["request_id"] == "req_abc"
    assert payload["message"] == "pipeline stage done"


def test_health_echoes_incoming_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "req_from_client"})
    assert response.headers["x-request-id"] == "req_from_client"


def test_query_reuses_request_id_as_query_id(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    monkeypatch.setattr(
        "app.graphs.query_graph.retrieve_events",
        lambda question, events, **kwargs: events[:3],
    )
    headers = _auth(client)
    upload = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("lobby.mp4", fake_mp4_bytes(b"log-query"), "video/mp4")},
    )
    video_id = upload.json()["video_id"]
    query = client.post(
        "/api/query",
        headers={**headers, "X-Request-ID": "req_query_cycle"},
        json={"question": "Did anyone in a red jacket enter after 21:00?", "video_id": video_id},
    )
    assert query.status_code == 200
    assert query.headers["x-request-id"] == "req_query_cycle"
    assert query.headers["x-query-id"] == "req_query_cycle"
    assert query.json()["query_id"] == "req_query_cycle"


def test_video_id_from_path() -> None:
    assert video_id_from_path("/api/videos/vid_abc123/status") == "vid_abc123"
    assert video_id_from_path("/api/videos") is None
    assert video_id_from_path("/api/query") is None

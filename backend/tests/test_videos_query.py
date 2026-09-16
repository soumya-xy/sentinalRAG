import pytest
from fastapi.testclient import TestClient

from tests.fakes import complete_ingest_for_tests


def _auth(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"email": "demo@sentinelrag.dev", "password": "demo1234"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_status_events_and_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    monkeypatch.setattr(
        "app.graphs.query_graph.retrieve_events",
        lambda question, events, **kwargs: events[:3],
    )

    headers = _auth(client)
    upload = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("lobby.mp4", b"fake-video-bytes", "video/mp4")},
        data={"camera_id": "cam-01"},
    )
    assert upload.status_code == 201
    video_id = upload.json()["video_id"]
    assert upload.json()["camera_id"] == "cam-01"
    assert upload.json()["status"] == "ready"

    status = client.get(f"/api/videos/{video_id}/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "ready"
    assert len(status.json()["stages"]) == 6

    events = client.get(f"/api/videos/{video_id}/events", headers=headers)
    assert events.status_code == 200
    body = events.json()
    assert body["count"] >= 1
    event = body["events"][0]
    for key in (
        "event_id",
        "video_id",
        "camera_id",
        "start_timestamp",
        "end_timestamp",
        "caption",
        "detected_classes",
        "bounding_boxes",
        "thumbnail_path",
        "confidence_score",
    ):
        assert key in event

    query = client.post(
        "/api/query",
        headers=headers,
        json={"question": "Did anyone in a red jacket enter after 21:00?", "video_id": video_id},
    )
    assert query.status_code == 200
    payload = query.json()
    assert payload["answer"]
    assert payload["citations"]
    assert payload["citations"][0]["video_id"] == video_id
    assert payload["citations"][0]["camera_id"] == "cam-01"


def test_events_before_ready_conflict(client: TestClient) -> None:
    headers = _auth(client)
    upload = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", b"bytes", "video/mp4")},
    )
    video_id = upload.json()["video_id"]
    assert upload.json()["status"] == "uploaded"
    events = client.get(f"/api/videos/{video_id}/events", headers=headers)
    assert events.status_code == 409


def test_media_requires_auth(client: TestClient) -> None:
    response = client.get("/api/media/vid_missing/evt_test01.jpg")
    assert response.status_code == 401


def test_media_hides_foreign_or_missing_video(client: TestClient) -> None:
    headers = _auth(client)
    response = client.get("/api/media/vid_missing/evt_test01.jpg", headers=headers)
    assert response.status_code == 404


def test_retry_rejected_unless_failed(client: TestClient) -> None:
    headers = _auth(client)
    upload = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", b"bytes", "video/mp4")},
    )
    video_id = upload.json()["video_id"]
    retry = client.post(f"/api/videos/{video_id}/retry", headers=headers)
    assert retry.status_code == 409


def test_retry_failed_ingest(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    headers = _auth(client)
    upload = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", b"bytes", "video/mp4")},
    )
    video_id = upload.json()["video_id"]
    from app.services.store import store

    store.fail_pipeline(video_id, "forced failure", failed_key="detect")
    retry = client.post(f"/api/videos/{video_id}/retry", headers=headers)
    assert retry.status_code == 200
    assert retry.json()["status"] == "ready"
    events = client.get(f"/api/videos/{video_id}/events", headers=headers)
    assert events.status_code == 200
    assert events.json()["count"] >= 1

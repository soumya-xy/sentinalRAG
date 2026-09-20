import pytest
from fastapi.testclient import TestClient

from tests.fakes import complete_ingest_for_tests, fake_avi_bytes, fake_jpeg_bytes, fake_mp4_bytes


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
        files={"file": ("lobby.mp4", fake_mp4_bytes(b"fake-video-bytes"), "video/mp4")},
        data={"camera_id": "cam-01"},
    )
    assert upload.status_code == 201
    video_id = upload.json()["video_id"]
    assert upload.json()["camera_id"] == "cam-01"
    assert upload.json()["status"] == "ready"
    assert upload.json()["duplicate"] is False
    assert upload.json()["content_hash"]

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
        files={"file": ("clip.mp4", fake_mp4_bytes(b"bytes"), "video/mp4")},
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
        files={"file": ("clip.mp4", fake_mp4_bytes(b"bytes"), "video/mp4")},
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
        files={"file": ("clip.mp4", fake_mp4_bytes(b"bytes"), "video/mp4")},
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


def test_duplicate_ready_upload_returns_existing_video(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def track(video_id: str) -> None:
        calls.append(video_id)
        complete_ingest_for_tests(video_id)

    monkeypatch.setattr("app.api.videos.enqueue_ingest", track)
    headers = _auth(client)
    first = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("lobby.mp4", fake_mp4_bytes(b"same-bytes"), "video/mp4")},
        data={"camera_id": "cam-01"},
    )
    second = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("lobby-copy.mp4", fake_mp4_bytes(b"same-bytes"), "video/mp4")},
        data={"camera_id": "cam-09"},
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["video_id"] == first.json()["video_id"]
    assert second.json()["status"] == "ready"
    assert second.json()["content_hash"] == first.json()["content_hash"]
    assert len(calls) == 1
    listed = client.get(f"/api/videos/{first.json()['video_id']}/events", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1


def test_failed_hash_match_is_reprocessed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", lambda _video_id: None)
    headers = _auth(client)
    first = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", fake_mp4_bytes(b"retry-bytes"), "video/mp4")},
    )
    video_id = first.json()["video_id"]
    from app.services.store import store

    store.fail_pipeline(video_id, "forced failure", failed_key="detect")
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    second = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", fake_mp4_bytes(b"retry-bytes"), "video/mp4")},
    )
    assert second.status_code == 201
    assert second.json()["duplicate"] is False
    assert second.json()["video_id"] == video_id
    assert second.json()["status"] == "ready"
    events = client.get(f"/api/videos/{video_id}/events", headers=headers)
    assert events.status_code == 200
    assert events.json()["count"] >= 1


def test_incomplete_hash_match_is_reprocessed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", lambda _video_id: None)
    headers = _auth(client)
    first = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", fake_mp4_bytes(b"incomplete-bytes"), "video/mp4")},
    )
    assert first.json()["status"] == "uploaded"
    video_id = first.json()["video_id"]
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    second = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", fake_mp4_bytes(b"incomplete-bytes"), "video/mp4")},
    )
    assert second.status_code == 201
    assert second.json()["duplicate"] is False
    assert second.json()["video_id"] == video_id
    assert second.json()["status"] == "ready"


def test_different_bytes_create_new_video(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    headers = _auth(client)
    first = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("a.mp4", fake_mp4_bytes(b"bytes-a"), "video/mp4")},
    )
    second = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("b.mp4", fake_mp4_bytes(b"bytes-b"), "video/mp4")},
    )
    assert first.json()["video_id"] != second.json()["video_id"]
    assert first.json()["content_hash"] != second.json()["content_hash"]
    assert second.json()["duplicate"] is False


def test_upload_rejects_non_video_bytes_with_mp4_name(client: TestClient) -> None:
    headers = _auth(client)
    response = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", fake_jpeg_bytes(), "video/mp4")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "JPEG image" in detail
    assert ".mp4" in detail
    assert "Traceback" not in detail


def test_upload_rejects_extension_signature_mismatch(client: TestClient) -> None:
    headers = _auth(client)
    response = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.avi", fake_mp4_bytes(), "video/x-msvideo")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert ".avi" in detail
    assert "MP4" in detail
    assert "Traceback" not in detail


def test_upload_rejects_unknown_bytes_as_mp4(client: TestClient) -> None:
    headers = _auth(client)
    response = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.mp4", b"this-is-not-a-container", "video/mp4")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Could not recognize a video container" in detail
    assert "Traceback" not in detail


def test_upload_accepts_avi_when_signature_matches(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.videos.enqueue_ingest", complete_ingest_for_tests)
    headers = _auth(client)
    response = client.post(
        "/api/videos",
        headers=headers,
        files={"file": ("clip.avi", fake_avi_bytes(), "video/x-msvideo")},
    )
    assert response.status_code == 201
    assert response.json()["duplicate"] is False

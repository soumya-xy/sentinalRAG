import logging

import pytest

from app.core.config import reset_settings_cache
from app.models.event import BoundingBox, EventRecord
from app.services.catalog_types import VideoInternal, now_utc
from app.services.embedding_meta import current_embedding_model, stamp_events
from app.services.memory_store import MemoryCatalog
from app.services.retrieval import retrieve_events, warn_if_embedding_model_mismatch


def _event(event_id: str = "evt_1", *, embedding_model: str | None = None) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        video_id="vid_1",
        camera_id="cam-01",
        start_timestamp="00:00:01",
        end_timestamp="00:00:04",
        caption="Person in a red jacket standing near the lobby doors.",
        detected_classes=["person"],
        bounding_boxes=[BoundingBox(x=10, y=10, w=40, h=80, frame_timestamp="00:00:02")],
        thumbnail_path="memory/x.jpg",
        confidence_score=0.9,
        embedding_model=embedding_model,
    )


def test_active_embedding_model_comes_from_google_config() -> None:
    reset_settings_cache()
    assert current_embedding_model() == "text-embedding-004"


def test_stamp_events_uses_config_not_caller_value() -> None:
    reset_settings_cache()
    stamped = stamp_events([_event(embedding_model="caller-hardcoded")])
    assert stamped[0].embedding_model == "text-embedding-004"
    assert stamped[0].embedding_model_version is None


def test_memory_catalog_stamps_model_on_write() -> None:
    reset_settings_cache()
    catalog = MemoryCatalog()
    catalog.put_video(
        VideoInternal(
            video_id="vid_1",
            user_id="usr_1",
            camera_id="cam-01",
            filename="clip.mp4",
            original_filename="clip.mp4",
            stored_path="memory/clip.mp4",
            status="processing",
            created_at=now_utc(),
            size_bytes=12,
        )
    )
    catalog.set_events("vid_1", [_event(embedding_model=None)])
    stored = catalog.get_events("vid_1")[0]
    assert stored.embedding_model == "text-embedding-004"


def test_mismatch_logs_warning_not_failure(caplog: pytest.LogCaptureFixture) -> None:
    events = [_event(embedding_model="BAAI/bge-m3")]
    with caplog.at_level(logging.WARNING, logger="sentinelrag.retrieval"):
        warn_if_embedding_model_mismatch(events)
    assert "does not match the majority stored model" in caplog.text
    assert "BAAI/bge-m3" in caplog.text


def test_matching_model_does_not_warn(caplog: pytest.LogCaptureFixture) -> None:
    events = [_event(embedding_model="text-embedding-004")]
    with caplog.at_level(logging.WARNING, logger="sentinelrag.retrieval"):
        warn_if_embedding_model_mismatch(events)
    assert caplog.text == ""


def test_unlabeled_events_do_not_warn(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="sentinelrag.retrieval"):
        warn_if_embedding_model_mismatch([_event()])
    assert caplog.text == ""


def test_version_mismatch_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        "app.services.retrieval.current_embedding_model_version",
        lambda: "2",
    )
    event = _event(embedding_model="text-embedding-004")
    event = event.model_copy(update={"embedding_model_version": "1"})
    with caplog.at_level(logging.WARNING, logger="sentinelrag.retrieval"):
        warn_if_embedding_model_mismatch([event])
    assert "version" in caplog.text
    assert "'1'" in caplog.text


def test_retrieve_events_still_returns_on_model_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    event = _event(embedding_model="BAAI/bge-m3")
    monkeypatch.setattr("app.services.retrieval.embed_query", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        "app.services.retrieval.store.match_events",
        lambda *_args, **_kwargs: [(event.event_id, 0.12)],
    )
    with caplog.at_level(logging.WARNING, logger="sentinelrag.retrieval"):
        result = retrieve_events("red jacket near the doors", [event], video_id="vid_1")
    assert [item.event_id for item in result] == ["evt_1"]
    assert "does not match the majority stored model" in caplog.text

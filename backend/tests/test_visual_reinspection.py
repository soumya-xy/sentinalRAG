import logging
from types import SimpleNamespace

import pytest

from app.graphs.query_graph import _compose
from app.models.event import BoundingBox, EventRecord


def _event() -> EventRecord:
    return EventRecord(
        event_id="evt_1",
        video_id="vid_1",
        camera_id="cam-01",
        start_timestamp="00:00:01",
        end_timestamp="00:00:04",
        caption="A person in a red jacket stands near the door.",
        detected_classes=["person"],
        bounding_boxes=[BoundingBox(x=1, y=1, w=10, h=10, frame_timestamp="00:00:02")],
        thumbnail_path="thumb/evt_1.jpg",
        confidence_score=0.9,
    )


class FakeLLM:
    def __init__(self, *, vision_failures: int = 0) -> None:
        self.vision_failures = vision_failures
        self.text_calls = 0
        self.vision_calls = 0

    def invoke(self, payload):
        is_vision = isinstance(payload, list)
        if is_vision:
            self.vision_calls += 1
            if self.vision_failures > 0:
                self.vision_failures -= 1
                exc = Exception("rate limited")
                exc.status_code = 429  # type: ignore[attr-defined]
                raise exc
            return SimpleNamespace(content="vision answer")
        self.text_calls += 1
        return SimpleNamespace(content="pass-1 text answer")


def test_visual_reinspection_returns_pass1_and_flag(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr("app.services.gemini_retry.time.sleep", lambda _d: None)
    llm = FakeLLM(vision_failures=99)
    monkeypatch.setattr("app.graphs.query_graph.get_chat_model", lambda: llm)
    monkeypatch.setattr(
        "app.graphs.query_graph._get_event_image_b64",
        lambda _event: "dGVzdA==",
    )
    state = {
        "question": "Was anyone in a red jacket visible?",
        "video_id": "vid_1",
        "camera_id": "cam-01",
        "query_id": "qry_test01",
        "retrieved": [_event()],
    }
    with caplog.at_level(logging.WARNING, logger="sentinelrag.query"):
        result = _compose(state)
    assert result["answer"] == "pass-1 text answer"
    assert result["answer_source"] == "llm"
    assert result["visual_reinspection_skipped"] is True
    assert llm.text_calls == 1
    assert llm.vision_calls == 3
    assert "Visual re-inspection skipped after retries" in caplog.text
    assert "video_id=vid_1" in caplog.text
    assert "query_id=qry_test01" in caplog.text


def test_visual_reinspection_succeeds_after_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.gemini_retry.time.sleep", lambda _d: None)
    llm = FakeLLM(vision_failures=1)
    monkeypatch.setattr("app.graphs.query_graph.get_chat_model", lambda: llm)
    monkeypatch.setattr(
        "app.graphs.query_graph._get_event_image_b64",
        lambda _event: "dGVzdA==",
    )
    result = _compose(
        {
            "question": "red jacket?",
            "video_id": "vid_1",
            "camera_id": "cam-01",
            "query_id": "qry_ok",
            "retrieved": [_event()],
        }
    )
    assert result["answer"] == "vision answer"
    assert result["visual_reinspection_skipped"] is False
    assert llm.vision_calls == 2

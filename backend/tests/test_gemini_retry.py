import logging

import pytest

from app.pipeline.caption import EventCaptioner
from app.pipeline.types import EventDraft
from app.services.gemini_retry import call_with_backoff, is_transient_error
from tests.test_caption import _draft


def _http_error(status: int, message: str = "boom") -> Exception:
    exc = Exception(message)
    exc.status_code = status  # type: ignore[attr-defined]
    return exc


def test_is_transient_for_429_and_5xx() -> None:
    assert is_transient_error(_http_error(429, "rate limit"))
    assert is_transient_error(_http_error(503, "unavailable"))
    assert is_transient_error(_http_error(500, "internal"))
    assert not is_transient_error(_http_error(400, "bad request"))
    assert not is_transient_error(ValueError("empty caption"))


def test_backoff_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("app.services.gemini_retry.time.sleep", sleeps.append)
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise _http_error(429, "rate limited")
        return "ok"

    with caplog.at_level(logging.WARNING, logger="sentinelrag.retry"):
        assert call_with_backoff(
            flaky,
            stage="caption_vision",
            video_id="vid_1",
            event_id="evt_1",
            attempts=3,
            base_delay=1.0,
        ) == "ok"
    assert calls["n"] == 3
    assert sleeps == [1.0, 2.0]
    assert "video_id=vid_1" in caplog.text
    assert "Retry 1/3" in caplog.text


def test_non_transient_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.gemini_retry.time.sleep", lambda _d: None)
    calls = {"n": 0}

    def bad() -> str:
        calls["n"] += 1
        raise ValueError("empty caption")

    with pytest.raises(ValueError):
        call_with_backoff(bad, stage="caption_vision", video_id="vid_1", attempts=3)
    assert calls["n"] == 1


def test_caption_falls_back_after_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path,
) -> None:
    monkeypatch.setattr("app.services.gemini_retry.time.sleep", lambda _d: None)
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"not-a-real-jpeg")
    monkeypatch.setattr(
        "app.pipeline.caption.crop_detection_jpeg",
        lambda *_args, **_kwargs: b"jpeg-bytes",
    )

    def always_429(*_args, **_kwargs) -> str:
        raise _http_error(429, "rate limited")

    monkeypatch.setattr("app.pipeline.caption.invoke_gemini_vision", always_429)
    draft = _draft(representative_image_path=image)
    with caplog.at_level(logging.WARNING, logger="sentinelrag.caption"):
        EventCaptioner()._caption_one(draft)
    assert draft.caption_source == "rule_based"
    assert "00:00:12–00:00:16" in draft.caption
    assert "Caption fallback to rule-based" in caplog.text
    assert "video_id=vid_1" in caplog.text
    assert "event_id=evt_1" in caplog.text

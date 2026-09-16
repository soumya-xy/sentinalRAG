from app.models.event import BoundingBox
from app.pipeline.caption import clip_caption, rule_based_caption
from app.pipeline.types import EventDraft


def _draft(**overrides: object) -> EventDraft:
    payload = {
        "event_id": "evt_1",
        "video_id": "vid_1",
        "camera_id": "cam-01",
        "start_timestamp": "00:00:12",
        "end_timestamp": "00:00:16",
        "detected_classes": ["person"],
        "bounding_boxes": [BoundingBox(x=10, y=260, w=40, h=80, frame_timestamp="00:00:14")],
        "confidence_score": 0.81,
        "representative_timestamp": "00:00:14",
        "object_count": 2,
    }
    payload.update(overrides)
    return EventDraft(**payload)  # type: ignore[arg-type]


def test_rule_based_caption_includes_count_confidence_and_window() -> None:
    text = rule_based_caption(_draft())
    assert "Person ×2" in text
    assert "00:00:12–00:00:16" in text
    assert "cam-01" in text
    assert "0.81" in text


def test_rule_based_caption_adds_position_when_frame_size_known() -> None:
    text = rule_based_caption(_draft(), image_size=(640, 360))
    assert "bottom-left" in text


def test_clip_caption_keeps_short_text() -> None:
    assert clip_caption("A person in a red jacket walks left.") == "A person in a red jacket walks left."


def test_clip_caption_cuts_on_sentence() -> None:
    long = ("A person in a red jacket walks across the lobby. " * 20).strip()
    clipped = clip_caption(long, max_chars=120)
    assert clipped.endswith(".")
    assert len(clipped) <= 120

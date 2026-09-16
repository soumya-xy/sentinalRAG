import pytest

from app.models.event import BoundingBox, EventRecord
from app.services.retrieval import parse_time_filter, retrieve_events


def _event(
    event_id: str,
    *,
    caption: str,
    classes: list[str],
    start: str,
    end: str,
    confidence: float = 0.9,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        video_id="vid_1",
        camera_id="cam-01",
        start_timestamp=start,
        end_timestamp=end,
        caption=caption,
        detected_classes=classes,
        bounding_boxes=[BoundingBox(x=10, y=10, w=40, h=80, frame_timestamp=start)],
        thumbnail_path="memory/x.jpg",
        confidence_score=confidence,
    )


PERSON = _event(
    "evt_person",
    caption="Person in a red jacket standing near the lobby doors.",
    classes=["person"],
    start="00:00:04",
    end="00:00:08",
)
CAR = _event(
    "evt_car",
    caption="A white car waiting at the curb.",
    classes=["car"],
    start="00:00:50",
    end="00:00:54",
)


def test_floor_drops_weak_unrelated_vector_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.retrieval.embed_query", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        "app.services.retrieval.store.match_events",
        lambda *_args, **_kwargs: [(PERSON.event_id, 0.11)],
    )
    assert retrieve_events("unrelated astronomy nebula", [PERSON], video_id="vid_1") == []


def test_lexical_rescues_low_vector_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.retrieval.embed_query", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        "app.services.retrieval.store.match_events",
        lambda *_args, **_kwargs: [(PERSON.event_id, 0.12)],
    )
    result = retrieve_events("red jacket near the doors", [PERSON], video_id="vid_1")
    assert [event.event_id for event in result] == ["evt_person"]


def test_hybrid_prefers_matching_class(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.retrieval.embed_query", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        "app.services.retrieval.store.match_events",
        lambda *_args, **_kwargs: [(PERSON.event_id, 0.72), (CAR.event_id, 0.41)],
    )
    result = retrieve_events("was a vehicle present", [PERSON, CAR], video_id="vid_1")
    assert result[0].event_id == "evt_car"


def test_last_seconds_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.retrieval.embed_query", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        "app.services.retrieval.store.match_events",
        lambda *_args, **_kwargs: [(PERSON.event_id, 0.7), (CAR.event_id, 0.7)],
    )
    result = retrieve_events("what happened in the last 10 seconds", [PERSON, CAR], video_id="vid_1")
    assert [event.event_id for event in result] == ["evt_car"]


def test_wall_clock_after_is_not_treated_as_video_time() -> None:
    window = parse_time_filter("Did anyone enter after 21:00?", [PERSON, CAR])
    assert window is None


def test_video_relative_after_is_parsed() -> None:
    window = parse_time_filter("anything after 00:00:20", [PERSON, CAR])
    assert window is not None
    assert window.start_seconds == 20

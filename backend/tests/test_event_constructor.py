from app.models.event import BoundingBox
from app.pipeline.events import EventConstructor
from app.pipeline.types import Detection, SampledFrame


def _frame(index: int, seconds: float) -> SampledFrame:
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return SampledFrame(
        frame_index=index,
        timestamp_seconds=seconds,
        timestamp_label=f"{hours:02d}:{minutes:02d}:{secs:02d}",
    )


def _det(
    frame: SampledFrame,
    *,
    label: str = "person",
    x: float,
    y: float = 40,
    w: float = 50,
    h: float = 120,
    confidence: float = 0.9,
) -> Detection:
    return Detection(
        frame=frame,
        label=label,
        confidence=confidence,
        box=BoundingBox(x=x, y=y, w=w, h=h, frame_timestamp=frame.timestamp_label),
        interesting=True,
    )


def test_far_apart_same_frame_are_separate_events() -> None:
    frame = _frame(0, 1.0)
    drafts = EventConstructor().construct(
        [_det(frame, x=20), _det(frame, x=400)],
        video_id="vid_1",
        camera_id="cam-01",
    )
    assert len(drafts) == 2
    assert all(draft.detected_classes == ["person"] for draft in drafts)
    assert all(draft.object_count == 2 for draft in drafts)


def test_nearby_boxes_across_frames_merge() -> None:
    drafts = EventConstructor().construct(
        [
            _det(_frame(0, 1.0), x=80),
            _det(_frame(1, 2.0), x=92),
            _det(_frame(2, 3.2), x=100),
        ],
        video_id="vid_1",
        camera_id="cam-01",
    )
    assert len(drafts) == 1
    assert drafts[0].start_timestamp == "00:00:01"
    assert drafts[0].end_timestamp == "00:00:03"
    assert len(drafts[0].bounding_boxes) >= 2
    assert drafts[0].object_count == 1


def test_temporal_gap_splits_track() -> None:
    drafts = EventConstructor().construct(
        [
            _det(_frame(0, 1.0), x=80),
            _det(_frame(1, 10.0), x=82),
        ],
        video_id="vid_1",
        camera_id="cam-01",
        gap_seconds=4.0,
    )
    assert len(drafts) == 2


def test_end_time_is_not_padded_by_three_seconds() -> None:
    drafts = EventConstructor().construct(
        [_det(_frame(0, 5.0), x=80)],
        video_id="vid_1",
        camera_id="cam-01",
    )
    assert drafts[0].start_timestamp == "00:00:05"
    assert drafts[0].end_timestamp == "00:00:05"


def test_tiny_boxes_are_ignored() -> None:
    frame = _frame(0, 1.0)
    drafts = EventConstructor().construct(
        [
            Detection(
                frame=frame,
                label="person",
                confidence=0.9,
                box=BoundingBox(x=10, y=10, w=5, h=5, frame_timestamp=frame.timestamp_label),
                interesting=True,
            )
        ],
        video_id="vid_1",
        camera_id="cam-01",
    )
    assert drafts == []

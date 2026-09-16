from app.models.event import BoundingBox, EventRecord


def test_event_schema_requires_phase1_fields() -> None:
    event = EventRecord(
        event_id="evt_test",
        video_id="vid_test",
        camera_id="cam-01",
        start_timestamp="00:14:20",
        end_timestamp="00:14:45",
        caption="A person wearing a red jacket enters the lobby.",
        detected_classes=["person"],
        bounding_boxes=[
            BoundingBox(x=92, y=34, w=58, h=130, frame_timestamp="00:14:22"),
        ],
        thumbnail_path="memory/vid_test/evt_test.svg",
        confidence_score=0.93,
    )
    dumped = event.model_dump()
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
        "object_count",
    ):
        assert key in dumped
        assert dumped[key] is not None
        if key != "confidence_score":
            assert dumped[key] != ""

from app.models.event import BoundingBox, EventRecord
from app.services.store import store


def fake_mp4_bytes(tag: bytes = b"test") -> bytes:
    """Minimal ISO BMFF `ftyp` box so upload sniffing accepts the payload."""
    header = bytearray(32)
    header[0:4] = (32).to_bytes(4, "big")
    header[4:8] = b"ftyp"
    header[8:12] = b"mp42"
    header[16:20] = b"mp42"
    header[20:24] = b"isom"
    return bytes(header) + tag


def fake_avi_bytes() -> bytes:
    return b"RIFF" + (32).to_bytes(4, "little") + b"AVI LIST" + b"\x00" * 16


def fake_jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 24


def fake_event(video_id: str, camera_id: str) -> EventRecord:
    return EventRecord(
        event_id="evt_test01",
        video_id=video_id,
        camera_id=camera_id,
        start_timestamp="00:00:14",
        end_timestamp="00:00:28",
        caption="A person wearing a red jacket enters through the main doors.",
        detected_classes=["person"],
        bounding_boxes=[
            BoundingBox(x=92, y=34, w=58, h=130, frame_timestamp="00:00:18"),
        ],
        thumbnail_path="memory/vid_test/evt_test01.jpg",
        confidence_score=0.91,
        thumbnail_url=f"/api/media/{video_id}/evt_test01.jpg",
        caption_source="rule_based",
        object_count=1,
    )


def complete_ingest_for_tests(video_id: str) -> None:
    video = store.get_video(video_id)
    if video is None:
        return
    store.begin_pipeline(video_id)
    store.set_events(video_id, [fake_event(video.video_id, video.camera_id)])


def skip_ingest_for_tests(_video_id: str) -> None:
    return

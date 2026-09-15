"""Orchestrates the batch ingest path: sample → detect → events → caption → index."""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.models.event import EventRecord
from app.pipeline.caption import EventCaptioner
from app.pipeline.detect import ObjectDetector
from app.pipeline.events import EventConstructor
from app.pipeline.index import EventIndexer
from app.pipeline.sampling import FrameSampler
from app.services.store import VideoInternal
from app.services.thumbnails import write_event_thumbnail


def thumbnail_url(video_id: str, event_id: str) -> str:
    return f"/api/media/{video_id}/{event_id}.svg"


def run_ingest_pipeline(video: VideoInternal) -> list[EventRecord]:
    """Run stub pipeline stages and materialize demo events + thumbnails.

    Replace each collaborator with the real YOLO / Qwen / Chroma class
    without changing this function signature.
    """
    settings = get_settings()
    sampler = FrameSampler()
    detector = ObjectDetector()
    constructor = EventConstructor()
    captioner = EventCaptioner()
    indexer = EventIndexer()

    duration = video.duration_seconds or 1020.0
    frames = sampler.sample(Path(video.stored_path), duration_seconds=duration)
    detections = detector.detect(frames)
    drafts = constructor.construct(
        detections,
        video_id=video.video_id,
        camera_id=video.camera_id,
    )
    drafts = captioner.caption(drafts, frames)

    records: list[EventRecord] = []
    for draft in drafts:
        thumb_path = write_event_thumbnail(
            video_id=video.video_id,
            event_id=draft.event_id,
            camera_id=video.camera_id,
            timestamp=draft.start_timestamp,
            label=", ".join(draft.detected_classes),
            boxes=draft.bounding_boxes,
        )
        records.append(
            EventRecord(
                event_id=draft.event_id,
                video_id=video.video_id,
                camera_id=video.camera_id,
                start_timestamp=draft.start_timestamp,
                end_timestamp=draft.end_timestamp,
                caption=draft.caption,
                detected_classes=draft.detected_classes,
                bounding_boxes=draft.bounding_boxes,
                thumbnail_path=thumb_path,
                confidence_score=draft.confidence_score,
                thumbnail_url=thumbnail_url(video.video_id, draft.event_id),
                caption_source=draft.caption_source,
            )
        )

    indexer.upsert(records)
    _ = settings.embedding_model_name
    return records

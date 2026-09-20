"""Orchestrates the batch ingest path: sample → detect → events → caption → index."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from app.core.config import get_settings
from app.models.event import EventRecord
from app.pipeline.caption import EventCaptioner
from app.pipeline.detect import ObjectDetector
from app.pipeline.events import EventConstructor
from app.pipeline.index import EventIndexer
from app.pipeline.sampling import FrameSampler
from app.services.object_storage import download_video_to, upload_thumbnail
from app.services.store import VideoInternal
from app.services.thumbnails import render_event_thumbnail

logger = logging.getLogger("sentinelrag.runner")

ProgressFn = Callable[[str, float, str], None]


def thumbnail_url(video_id: str, event_id: str, suffix: str = ".jpg") -> str:
    safe = suffix if suffix.startswith(".") else f".{suffix}"
    return f"/api/media/{video_id}/{event_id}{safe}"


def _local_video_path(video: VideoInternal, work_dir: Path) -> Path:
    settings = get_settings()
    suffix = Path(video.filename).suffix or ".mp4"
    dest = work_dir / f"{video.video_id}{suffix}"
    if settings.supabase_enabled:
        download_video_to(video.stored_path, dest)
        return dest
    source = Path(video.stored_path)
    if source.is_file():
        return source
    dest.write_bytes(b"")
    return dest


def run_ingest_pipeline(
    video: VideoInternal,
    on_progress: ProgressFn | None = None,
) -> list[EventRecord]:
    def mark(stage: str, progress: float, state: str = "running") -> None:
        if on_progress:
            on_progress(stage, progress, state)

    settings = get_settings()
    sampler = FrameSampler()
    detector = ObjectDetector()
    constructor = EventConstructor()
    captioner = EventCaptioner()
    indexer = EventIndexer()

    with tempfile.TemporaryDirectory(prefix="sentinelrag-") as tmp:
        work_dir = Path(tmp)
        local_video = _local_video_path(video, work_dir)

        mark("sample", 10, "running")
        frames = sampler.sample(local_video, video_id=video.video_id, work_dir=work_dir)
        if not frames:
            raise RuntimeError(
                "No frames could be sampled. The file may not be a readable video."
            )
        mark("sample", 100, "complete")

        mark("detect", 10, "running")
        detections = detector.detect(frames)
        mark("detect", 100, "complete")

        mark("events", 10, "running")
        drafts = constructor.construct(
            detections,
            video_id=video.video_id,
            camera_id=video.camera_id,
        )
        mark("events", 100, "complete")

        mark("caption", 10, "running")
        drafts = captioner.caption(drafts, frames)
        mark("caption", 100, "complete")

        mark("index", 10, "running")
        records: list[EventRecord] = []
        for draft in drafts:
            payload, suffix, content_type = render_event_thumbnail(
                camera_id=video.camera_id,
                timestamp=draft.start_timestamp,
                label=", ".join(draft.detected_classes),
                boxes=draft.bounding_boxes,
                image_path=draft.representative_image_path,
            )
            if settings.supabase_enabled:
                thumb_path = upload_thumbnail(
                    video.user_id,
                    video.video_id,
                    draft.event_id,
                    payload,
                    suffix=suffix,
                    content_type=content_type,
                )
            else:
                thumb_path = f"memory/{video.video_id}/{draft.event_id}{suffix}"
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
                    thumbnail_url=(
                        None
                        if settings.supabase_enabled
                        else thumbnail_url(video.video_id, draft.event_id, suffix)
                    ),
                    caption_source=draft.caption_source,
                    object_count=draft.object_count,
                )
            )

        indexer.upsert(records, video_id=video.video_id)
        mark("index", 100, "complete")
        logger.info("Ingest finished event_count=%s", len(records))
        return records

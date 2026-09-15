from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.video import PipelineStage, VideoStatus, VideoStatusResponse
from app.pipeline.runner import run_ingest_pipeline
from app.services.store import VideoInternal, store

PIPELINE_STAGES: list[tuple[str, str]] = [
    ("ingest", "Upload & ingest"),
    ("sample", "Frame sampling"),
    ("detect", "Detection — YOLO11"),
    ("events", "Event construction"),
    ("caption", "Captioning — Qwen2.5-VL"),
    ("index", "Index — ChromaDB"),
]


def _elapsed(video: VideoInternal) -> float:
    created = video.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - created).total_seconds())


def compute_status(video: VideoInternal) -> VideoStatusResponse:
    settings = get_settings()
    total = settings.mock_processing_seconds
    elapsed = _elapsed(video)
    if total <= 0:
        total = 0.0

    if video.status == "failed":
        stages = [
            PipelineStage(key=key, label=label, state="failed" if index == 0 else "pending", progress=0)
            for index, (key, label) in enumerate(PIPELINE_STAGES)
        ]
        return VideoStatusResponse(
            video_id=video.video_id,
            status="failed",
            current_stage=None,
            progress=0,
            stages=stages,
            error=video.error or "Processing failed",
            caption_mode="rule_based" if settings.vlm_use_rule_based_fallback else "vlm",
        )

    raw_progress = 100.0 if total <= 0 else min(100.0, (elapsed / total) * 100.0)
    n = len(PIPELINE_STAGES)
    stage_span = 100.0 / n
    stages: list[PipelineStage] = []
    current: str | None = None

    if raw_progress >= 100:
        status: VideoStatus = "ready"
        for key, label in PIPELINE_STAGES:
            stages.append(PipelineStage(key=key, label=label, state="complete", progress=100))
        if not video.events_materialized:
            events = run_ingest_pipeline(video)
            store.set_events(video.video_id, events)
        else:
            store.set_video_status(video.video_id, "ready")
    else:
        status = "processing"
        store.set_video_status(video.video_id, "processing")
        active_index = min(n - 1, int(raw_progress // stage_span))
        current = PIPELINE_STAGES[active_index][0]
        for index, (key, label) in enumerate(PIPELINE_STAGES):
            if index < active_index:
                stages.append(PipelineStage(key=key, label=label, state="complete", progress=100))
            elif index == active_index:
                local = ((raw_progress - index * stage_span) / stage_span) * 100.0
                stages.append(
                    PipelineStage(key=key, label=label, state="running", progress=round(local, 1))
                )
            else:
                stages.append(PipelineStage(key=key, label=label, state="pending", progress=0))

    return VideoStatusResponse(
        video_id=video.video_id,
        status=status,
        current_stage=current,
        progress=round(raw_progress, 1),
        stages=stages,
        error=None,
        caption_mode="rule_based" if settings.vlm_use_rule_based_fallback else "vlm",
    )

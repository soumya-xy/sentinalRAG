from __future__ import annotations

import logging
import threading
from contextvars import copy_context

from app.core.config import get_settings
from app.core.context import bind_log_context, set_video_id
from app.models.video import PipelineStage, VideoStatusResponse
from app.pipeline.runner import run_ingest_pipeline
from app.services.store import PIPELINE_STAGES, VideoInternal, store

logger = logging.getLogger("sentinelrag.processing")


def caption_mode() -> str:
    settings = get_settings()
    if (
        settings.vlm_provider == "gemini"
        and settings.google_api_key
        and not settings.vlm_use_rule_based_fallback
    ):
        return "vlm"
    return "rule_based"


def build_status(video: VideoInternal) -> VideoStatusResponse:
    if not video.stage_states:
        pending = [
            PipelineStage(key=key, label=label, state="pending", progress=0)
            for key, label in PIPELINE_STAGES
        ]
        return VideoStatusResponse(
            video_id=video.video_id,
            status=video.status,
            current_stage=video.current_stage,
            progress=video.overall_progress,
            stages=pending,
            error=video.error,
            caption_mode=caption_mode(),
        )

    stages = [
        PipelineStage(
            key=key,
            label=label,
            state=video.stage_states.get(key, "pending"),  # type: ignore[arg-type]
            progress=video.stage_progress.get(key, 0.0),
        )
        for key, label in PIPELINE_STAGES
    ]
    return VideoStatusResponse(
        video_id=video.video_id,
        status=video.status,
        current_stage=video.current_stage,
        progress=video.overall_progress,
        stages=stages,
        error=video.error,
        caption_mode=caption_mode(),
    )


def run_ingest_job(video_id: str) -> None:
    with bind_log_context(video_id=video_id):
        video = store.get_video(video_id)
        if video is None:
            logger.error("Ingest job skipped; video row is missing")
            return

        def on_progress(stage: str, progress: float, state: str) -> None:
            store.update_stage(video_id, stage, progress, state)
            logger.info("Pipeline stage=%s progress=%s state=%s", stage, progress, state)

        logger.info("Ingest job started")
        try:
            run_ingest_pipeline(video, on_progress=on_progress)
            logger.info("Ingest job finished")
        except Exception as exc:
            logger.exception("Ingest job failed")
            current = store.get_video(video_id)
            store.fail_pipeline(
                video_id,
                str(exc),
                failed_key=current.current_stage if current else None,
            )


def enqueue_ingest(video_id: str) -> None:
    set_video_id(video_id)
    store.begin_pipeline(video_id)
    logger.info("Ingest enqueued")
    if get_settings().ingest_in_background:
        ctx = copy_context()
        thread = threading.Thread(
            target=ctx.run,
            args=(run_ingest_job, video_id),
            daemon=True,
            name=f"ingest-{video_id}",
        )
        thread.start()
        return
    run_ingest_job(video_id)

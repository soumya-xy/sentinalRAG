from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.models.video import VideoStatus

PIPELINE_STAGES: list[tuple[str, str]] = [
    ("ingest", "Upload & ingest"),
    ("sample", "Frame sampling"),
    ("detect", "Detection — YOLO11"),
    ("events", "Event construction"),
    ("caption", "Captioning"),
    ("index", "Index — pgvector"),
]

STAGE_KEYS = [key for key, _ in PIPELINE_STAGES]


@dataclass
class UserRecord:
    user_id: str
    email: str
    display_name: str
    password_hash: str = ""


@dataclass
class VideoInternal:
    video_id: str
    user_id: str
    camera_id: str
    filename: str
    original_filename: str
    stored_path: str
    status: VideoStatus
    created_at: datetime
    size_bytes: int
    duration_seconds: float | None = None
    error: str | None = None
    events_materialized: bool = False
    current_stage: str | None = None
    overall_progress: float = 0.0
    stage_states: dict[str, str] = field(default_factory=dict)
    stage_progress: dict[str, float] = field(default_factory=dict)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


CaptionMode = Literal["vlm", "rule_based"]

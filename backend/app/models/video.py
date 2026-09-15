from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

VideoStatus = Literal["uploaded", "processing", "ready", "failed"]
StageState = Literal["pending", "running", "complete", "failed"]


class PipelineStage(BaseModel):
    key: str
    label: str
    state: StageState
    progress: float = Field(ge=0.0, le=100.0)


class VideoRecord(BaseModel):
    video_id: str
    camera_id: str
    filename: str
    original_filename: str
    status: VideoStatus
    duration_seconds: float | None = None
    created_at: datetime
    size_bytes: int = 0


class VideoListResponse(BaseModel):
    videos: list[VideoRecord]


class VideoStatusResponse(BaseModel):
    video_id: str
    status: VideoStatus
    current_stage: str | None = None
    progress: float = Field(ge=0.0, le=100.0)
    stages: list[PipelineStage]
    error: str | None = None
    caption_mode: str | None = None

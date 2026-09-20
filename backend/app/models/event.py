from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Pixel box on a representative (or per-frame) still."""

    x: float
    y: float
    w: float
    h: float
    frame_timestamp: str = Field(description="HH:MM:SS within the source video")


class EventRecord(BaseModel):
    """Indexed event contract — CLAUDE.md Section 6.

    `video_id` and `camera_id` are required in Phase 1 for Phase 2 compatibility.
    """

    event_id: str
    video_id: str
    camera_id: str
    start_timestamp: str
    end_timestamp: str
    caption: str
    detected_classes: list[str]
    bounding_boxes: list[BoundingBox]
    thumbnail_path: str = Field(
        description="Supabase Storage object key (or memory path in tests). Never image bytes."
    )
    confidence_score: float = Field(ge=0.0, le=1.0)
    thumbnail_url: str | None = Field(
        default=None,
        description="Ephemeral signed URL for API responses. Not persisted on the row.",
    )
    caption_source: str | None = Field(
        default=None,
        description="vlm | rule_based — which captioner produced the text",
    )
    object_count: int = Field(
        default=1,
        ge=1,
        description="Max same-class objects visible in this event's time window",
    )
    embedding_model: str | None = Field(
        default=None,
        description="Embedder that produced events.embedding, from app config at write time",
    )
    embedding_model_version: str | None = Field(
        default=None,
        description="Optional provider-specific embedder version; unset when the model id is enough",
    )


class EventListResponse(BaseModel):
    video_id: str
    camera_id: str
    count: int
    events: list[EventRecord]

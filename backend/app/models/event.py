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
    thumbnail_path: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    thumbnail_url: str | None = None
    caption_source: str | None = Field(
        default=None,
        description="vlm | rule_based — which captioner produced the text",
    )


class EventListResponse(BaseModel):
    video_id: str
    camera_id: str
    count: int
    events: list[EventRecord]

from dataclasses import dataclass, field

from app.models.event import BoundingBox


@dataclass
class SampledFrame:
    frame_index: int
    timestamp_seconds: float
    timestamp_label: str
    image_path: str | None = None


@dataclass
class Detection:
    frame: SampledFrame
    label: str
    confidence: float
    box: BoundingBox
    interesting: bool = True


@dataclass
class EventDraft:
    event_id: str
    video_id: str
    camera_id: str
    start_timestamp: str
    end_timestamp: str
    detected_classes: list[str]
    bounding_boxes: list[BoundingBox]
    confidence_score: float
    representative_timestamp: str
    caption: str = ""
    caption_source: str = "rule_based"
    thumbnail_path: str = ""
    notes: list[str] = field(default_factory=list)

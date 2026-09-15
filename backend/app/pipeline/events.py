"""2.3 Event construction — group consecutive detections into time-bounded events."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from app.core.config import get_settings
from app.pipeline.types import Detection, EventDraft


def _label(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class EventConstructor:
    def construct(
        self,
        detections: list[Detection],
        *,
        video_id: str,
        camera_id: str,
        gap_seconds: float | None = None,
    ) -> list[EventDraft]:
        """Merge nearby same-class detections into events.

        Spatial tracking is out of scope for Phase 1 (no track IDs yet).
        """
        if not detections:
            return []

        gap = gap_seconds if gap_seconds is not None else get_settings().event_gap_seconds
        by_class: dict[str, list[Detection]] = defaultdict(list)
        for detection in sorted(detections, key=lambda item: item.frame.timestamp_seconds):
            by_class[detection.label].append(detection)

        drafts: list[EventDraft] = []
        for label, items in by_class.items():
            cluster: list[Detection] = [items[0]]
            for item in items[1:]:
                if item.frame.timestamp_seconds - cluster[-1].frame.timestamp_seconds <= gap:
                    cluster.append(item)
                else:
                    drafts.append(self._to_draft(cluster, label, video_id, camera_id))
                    cluster = [item]
            drafts.append(self._to_draft(cluster, label, video_id, camera_id))

        drafts.sort(key=lambda draft: draft.start_timestamp)
        return drafts

    def _to_draft(
        self,
        cluster: list[Detection],
        label: str,
        video_id: str,
        camera_id: str,
    ) -> EventDraft:
        start = cluster[0].frame.timestamp_seconds
        end = cluster[-1].frame.timestamp_seconds
        mid = cluster[len(cluster) // 2]
        confidence = sum(item.confidence for item in cluster) / len(cluster)
        return EventDraft(
            event_id=f"evt_{uuid4().hex[:10]}",
            video_id=video_id,
            camera_id=camera_id,
            start_timestamp=_label(start),
            end_timestamp=_label(max(end, start + 3)),
            detected_classes=[label],
            bounding_boxes=[mid.box],
            confidence_score=round(confidence, 3),
            representative_timestamp=mid.frame.timestamp_label,
            representative_image_path=mid.frame.image_path,
            notes=[f"{len(cluster)} detections clustered"],
        )

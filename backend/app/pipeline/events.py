"""2.3 Event construction — spatial-temporal tracks, one object per event."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from app.core.config import get_settings
from app.models.event import BoundingBox
from app.pipeline.geometry import (
    box_area,
    box_iou,
    boxes_spatially_linked,
    timestamp_range_labels,
)
from app.pipeline.types import Detection, EventDraft


def _representative_boxes(cluster: list[Detection]) -> list[BoundingBox]:
    start_box = cluster[0].box
    mid_box = cluster[len(cluster) // 2].box
    end_box = cluster[-1].box
    chosen = [start_box]
    for box in (mid_box, end_box):
        if box is chosen[-1]:
            continue
        if box.frame_timestamp == chosen[-1].frame_timestamp and box_iou(box, chosen[-1]) > 0.95:
            continue
        chosen.append(box)
    return chosen


def _scene_count(label: str, start: float, end: float, detections: list[Detection]) -> int:
    per_frame: dict[int, int] = defaultdict(int)
    for item in detections:
        if item.label != label:
            continue
        t = item.frame.timestamp_seconds
        if start - 1e-6 <= t <= end + 1e-6:
            per_frame[item.frame.frame_index] += 1
    return max(per_frame.values()) if per_frame else 1


def _usable(detections: list[Detection], min_area: float) -> list[Detection]:
    kept: list[Detection] = []
    for item in detections:
        if not item.interesting:
            continue
        if box_area(item.box) < min_area:
            continue
        kept.append(item)
    return kept


class EventConstructor:
    def construct(
        self,
        detections: list[Detection],
        *,
        video_id: str,
        camera_id: str,
        gap_seconds: float | None = None,
    ) -> list[EventDraft]:
        """Track same-class boxes across time. Same-frame hits stay separate events."""
        settings = get_settings()
        gap = gap_seconds if gap_seconds is not None else settings.event_gap_seconds
        min_area = settings.event_min_box_area
        iou_min = settings.event_iou_min
        usable = _usable(detections, min_area)
        if not usable:
            return []

        by_class: dict[str, list[Detection]] = defaultdict(list)
        for detection in sorted(usable, key=lambda item: item.frame.timestamp_seconds):
            by_class[detection.label].append(detection)

        drafts: list[EventDraft] = []
        for label, items in by_class.items():
            for cluster in self._tracks(items, gap=gap, iou_min=iou_min):
                drafts.append(
                    self._to_draft(cluster, label, video_id, camera_id, usable)
                )

        drafts.sort(key=lambda draft: (draft.start_timestamp, draft.event_id))
        return drafts

    def _tracks(
        self,
        items: list[Detection],
        *,
        gap: float,
        iou_min: float,
    ) -> list[list[Detection]]:
        tracks: list[list[Detection]] = []
        for item in items:
            best_index = -1
            best_iou = -1.0
            for index, track in enumerate(tracks):
                last = track[-1]
                delta = item.frame.timestamp_seconds - last.frame.timestamp_seconds
                if delta <= 1e-6:
                    continue
                if delta > gap:
                    continue
                if not boxes_spatially_linked(item.box, last.box, iou_min=iou_min):
                    continue
                overlap = box_iou(item.box, last.box)
                if overlap > best_iou:
                    best_iou = overlap
                    best_index = index
            if best_index >= 0:
                tracks[best_index].append(item)
            else:
                tracks.append([item])
        return tracks

    def _to_draft(
        self,
        cluster: list[Detection],
        label: str,
        video_id: str,
        camera_id: str,
        all_usable: list[Detection],
    ) -> EventDraft:
        start = cluster[0].frame.timestamp_seconds
        end = cluster[-1].frame.timestamp_seconds
        start_label, end_label = timestamp_range_labels(start, end)
        mid = cluster[len(cluster) // 2]
        confidence = sum(item.confidence for item in cluster) / len(cluster)
        count = _scene_count(label, start, end, all_usable)
        boxes = _representative_boxes(cluster)
        return EventDraft(
            event_id=f"evt_{uuid4().hex[:10]}",
            video_id=video_id,
            camera_id=camera_id,
            start_timestamp=start_label,
            end_timestamp=end_label,
            detected_classes=[label],
            bounding_boxes=boxes,
            confidence_score=round(confidence, 3),
            representative_timestamp=mid.frame.timestamp_label,
            representative_image_path=mid.frame.image_path,
            object_count=count,
            notes=[
                f"{len(cluster)} detections tracked",
                f"scene_count={count}",
            ],
        )

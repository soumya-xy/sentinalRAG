"""Shared box/time helpers for event construction and captioning."""

from __future__ import annotations

import math

from app.models.event import BoundingBox


def timestamp_label(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def timestamp_range_labels(start_seconds: float, end_seconds: float) -> tuple[str, str]:
    """Honest window. If the span is sub-second, bump the end label by 1s so it is visible."""
    start = min(start_seconds, end_seconds)
    end = max(start_seconds, end_seconds)
    start_label = timestamp_label(start)
    end_label = timestamp_label(end)
    if end > start and end_label == start_label:
        end_label = timestamp_label(start + 1)
    return start_label, end_label


def seconds_from_label(label: str) -> float | None:
    parts = label.strip().split(":")
    if len(parts) == 2:
        parts = ["0", *parts]
    if len(parts) != 3:
        return None
    try:
        hours, minutes, secs = (int(part) for part in parts)
    except ValueError:
        return None
    if minutes > 59 or secs > 59 or hours < 0:
        return None
    return float(hours * 3600 + minutes * 60 + secs)


def box_center(box: BoundingBox) -> tuple[float, float]:
    return (box.x + box.w / 2.0, box.y + box.h / 2.0)


def box_area(box: BoundingBox) -> float:
    return max(0.0, box.w) * max(0.0, box.h)


def box_iou(a: BoundingBox, b: BoundingBox) -> float:
    ax2, ay2 = a.x + a.w, a.y + a.h
    bx2, by2 = b.x + b.w, b.y + b.h
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = box_area(a) + box_area(b) - inter
    if union <= 1e-6:
        return 0.0
    return inter / union


def boxes_spatially_linked(
    a: BoundingBox,
    b: BoundingBox,
    *,
    iou_min: float = 0.25,
    center_diag_ratio: float = 1.8,
) -> bool:
    """True if two boxes likely belong to the same object across nearby frames."""
    if box_iou(a, b) >= iou_min:
        return True
    c1, c2 = box_center(a), box_center(b)
    dist = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
    scale = max((math.hypot(a.w, a.h) + math.hypot(b.w, b.h)) / 2.0, 1.0)
    return dist <= center_diag_ratio * scale


def box_position_label(box: BoundingBox, image_size: tuple[int, int] | None) -> str:
    if image_size is None:
        return ""
    width, height = image_size
    if width <= 0 or height <= 0:
        return ""
    cx, cy = box_center(box)
    horiz = "left" if cx < width / 3 else ("right" if cx > 2 * width / 3 else "center")
    vert = "top" if cy < height / 3 else ("bottom" if cy > 2 * height / 3 else "mid")
    return f"{vert}-{horiz}"

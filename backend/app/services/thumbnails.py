from pathlib import Path

import cv2
import numpy as np

from app.models.event import BoundingBox


def render_thumbnail_svg(
    *,
    camera_id: str,
    timestamp: str,
    label: str,
    boxes: list[BoundingBox],
    width: int = 320,
    height: int = 180,
) -> str:
    rects = []
    for box in boxes:
        rects.append(
            (
                f'<rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" '
                f'fill="none" stroke="#8FA888" stroke-width="1.5"/>'
            )
        )
    box_markup = "\n  ".join(rects)
    safe_label = label.replace("&", "&amp;").replace("<", "&lt;")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#0D1210"/>
  <rect x="12" y="28" width="{width - 24}" height="{height - 40}" fill="#161C1A" stroke="#2A322E"/>
  <text x="12" y="18" fill="#8B9490" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">{camera_id}  {timestamp}</text>
  {box_markup}
  <text x="16" y="{height - 14}" fill="#E8E6DE" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">{safe_label}</text>
</svg>
"""


def render_event_thumbnail(
    *,
    camera_id: str,
    timestamp: str,
    label: str,
    boxes: list[BoundingBox],
    image_path: Path | None = None,
) -> tuple[bytes, str, str]:
    """Return (bytes, suffix, content_type). Does not write to disk."""
    if image_path is not None and image_path.exists():
        frame = cv2.imread(str(image_path))
        if frame is not None:
            for box in boxes:
                x1, y1 = int(box.x), int(box.y)
                x2, y2 = int(box.x + box.w), int(box.y + box.h)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (143, 168, 136), 2)
            ok, encoded = cv2.imencode(".jpg", frame)
            if ok:
                return encoded.tobytes(), ".jpg", "image/jpeg"

    svg = render_thumbnail_svg(
        camera_id=camera_id,
        timestamp=timestamp,
        label=label,
        boxes=boxes,
    )
    return svg.encode("utf-8"), ".svg", "image/svg+xml"


def encode_placeholder() -> tuple[bytes, str, str]:
    blank = np.zeros((180, 320, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", blank)
    if ok:
        return encoded.tobytes(), ".jpg", "image/jpeg"
    return b"", ".jpg", "image/jpeg"

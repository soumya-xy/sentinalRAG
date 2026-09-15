from app.models.event import BoundingBox
from app.services.storage import thumbnail_file_path


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


def write_event_thumbnail(
    *,
    video_id: str,
    event_id: str,
    camera_id: str,
    timestamp: str,
    label: str,
    boxes: list[BoundingBox],
) -> str:
    path = thumbnail_file_path(video_id, event_id)
    path.write_text(
        render_thumbnail_svg(
            camera_id=camera_id,
            timestamp=timestamp,
            label=label,
            boxes=boxes,
        ),
        encoding="utf-8",
    )
    return str(path)

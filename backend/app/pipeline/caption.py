"""2.4 Event captioning — bbox crop to Gemini, richer rule-based fallback."""

from __future__ import annotations

import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2

from app.core.config import get_settings
from app.models.event import BoundingBox
from app.pipeline.geometry import box_position_label
from app.pipeline.types import EventDraft, SampledFrame
from app.services.llm import invoke_gemini_vision, message_text

logger = logging.getLogger("sentinelrag.caption")

_CAPTION_PROMPT = (
    "You are an expert CCTV visual security analyst captioning a cropped detection for a search index.\n"
    "The image is a close crop around the detector box, plus a small amount of context.\n"
    "Describe only what is visible:\n"
    "1. SUBJECT: class, count, clothing colors, bags, and action (walking, standing, waiting).\n"
    "2. VEHICLES: type, color, motion if present.\n"
    "3. CONTEXT: readable signs or distinctive background only if visible in the crop.\n"
    "Write at most two factual sentences. No preamble, no intent, no off-screen guesses.\n"
    "Do not invent object classes that contradict the detector constraints unless they are clearly visible."
)


def clip_caption(text: str, max_chars: int = 420) -> str:
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return ""
    if len(cleaned) <= max_chars:
        return cleaned
    cut = cleaned[:max_chars]
    for sep in (". ", "! ", "? "):
        idx = cut.rfind(sep)
        if idx >= 80:
            return cut[: idx + 1].strip()
    trimmed = cut.rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{trimmed}."


def _image_size(image_path: Path | None) -> tuple[int, int] | None:
    if image_path is None or not image_path.exists():
        return None
    frame = cv2.imread(str(image_path))
    if frame is None:
        return None
    height, width = frame.shape[:2]
    return int(width), int(height)


def crop_detection_jpeg(
    image_path: Path,
    boxes: list[BoundingBox],
    *,
    pad_ratio: float = 0.35,
) -> bytes | None:
    frame = cv2.imread(str(image_path))
    if frame is None:
        return None
    height, width = frame.shape[:2]
    if boxes:
        box = boxes[min(len(boxes) // 2, len(boxes) - 1)]
        pad_x = max(16.0, box.w * pad_ratio)
        pad_y = max(16.0, box.h * pad_ratio)
        x1 = max(0, int(box.x - pad_x))
        y1 = max(0, int(box.y - pad_y))
        x2 = min(width, int(box.x + box.w + pad_x))
        y2 = min(height, int(box.y + box.h + pad_y))
        if x2 - x1 >= 40 and y2 - y1 >= 40:
            frame = frame[y1:y2, x1:x2]
    ok, encoded = cv2.imencode(".jpg", frame)
    if not ok:
        return None
    return encoded.tobytes()


def rule_based_caption(draft: EventDraft, image_size: tuple[int, int] | None = None) -> str:
    classes = ", ".join(draft.detected_classes) or "object"
    count = max(1, draft.object_count)
    subject = classes if count == 1 else f"{classes} ×{count}"
    box = draft.bounding_boxes[len(draft.bounding_boxes) // 2] if draft.bounding_boxes else None
    position = box_position_label(box, image_size) if box is not None else ""
    where = f" {position}" if position else ""
    return (
        f"{subject.capitalize()} at {draft.start_timestamp}–{draft.end_timestamp} "
        f"on {draft.camera_id}{where}, conf {draft.confidence_score:.2f}."
    )


def _detector_constraints(draft: EventDraft) -> str:
    box = draft.bounding_boxes[len(draft.bounding_boxes) // 2] if draft.bounding_boxes else None
    box_note = ""
    if box is not None:
        box_note = f" Representative box: {box.w:.0f}×{box.h:.0f}px at ({box.x:.0f},{box.y:.0f})."
    return (
        f"Camera: {draft.camera_id}. Window: {draft.start_timestamp}–{draft.end_timestamp}. "
        f"Detector labels: {', '.join(draft.detected_classes) or 'unknown'}. "
        f"Tracked subject count: 1. Same-class objects visible in this window: {draft.object_count}. "
        f"Detector confidence: {draft.confidence_score:.2f}.{box_note}"
    )


class EventCaptioner:
    def caption(self, drafts: list[EventDraft], frames: list[SampledFrame]) -> list[EventDraft]:
        _ = frames
        settings = get_settings()
        use_gemini = (
            settings.vlm_provider == "gemini"
            and not settings.vlm_use_rule_based_fallback
            and bool(settings.google_api_key)
        )
        if not use_gemini:
            return self._rule_based(drafts)
        return self._gemini(drafts)

    def _gemini(self, drafts: list[EventDraft]) -> list[EventDraft]:
        if not drafts:
            return drafts
        workers = min(3, len(drafts))
        if workers == 1:
            self._caption_one(drafts[0])
            return drafts
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(self._caption_one, draft) for draft in drafts]
            for future in as_completed(futures):
                future.result()
        return drafts

    def _caption_one(self, draft: EventDraft) -> None:
        image_path = draft.representative_image_path
        if image_path is None or not image_path.exists():
            self._apply_rule(draft)
            return
        payload_bytes = crop_detection_jpeg(image_path, draft.bounding_boxes)
        if payload_bytes is None:
            self._apply_rule(draft)
            return
        prompt = f"{_CAPTION_PROMPT}\n{_detector_constraints(draft)}"
        try:
            payload = base64.b64encode(payload_bytes).decode("ascii")
            response = invoke_gemini_vision(prompt, payload)
            text = clip_caption(message_text(response).strip())
            if not text:
                raise ValueError("empty caption")
            draft.caption = text
            draft.caption_source = "vlm"
        except Exception as exc:
            logger.warning("Gemini caption failed for %s: %s", draft.event_id, exc)
            self._apply_rule(draft)

    def _rule_based(self, drafts: list[EventDraft]) -> list[EventDraft]:
        for draft in drafts:
            self._apply_rule(draft)
        return drafts

    def _apply_rule(self, draft: EventDraft) -> None:
        draft.caption = rule_based_caption(draft, _image_size(draft.representative_image_path))
        draft.caption_source = "rule_based"

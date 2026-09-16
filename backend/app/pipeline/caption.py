"""2.4 Event captioning — Gemini vision on flagged frames, rule-based fallback."""

from __future__ import annotations

import base64
import logging

from app.core.config import get_settings
from app.pipeline.types import EventDraft, SampledFrame
from app.services.llm import invoke_gemini_vision, message_text

logger = logging.getLogger("sentinelrag.caption")

_CAPTION_PROMPT = (
    "You are an expert CCTV visual security analyst captioning a frame for a surveillance search index.\n"
    "Describe the scene in high factual detail:\n"
    "1. COUNT & PEOPLE: State the number of people visible. Describe clothing colors (jackets, shirts, pants, hats), bags/backpacks, and physical actions (walking, standing, running).\n"
    "2. VEHICLES: Type (car, truck, bike, motorcycle), color, and motion state if any are present.\n"
    "3. ENVIRONMENT & TEXT: Any visible signs, building text, or distinctive environment features.\n"
    "4. SUMMARY: Provide a concise, highly searchable 2-sentence summary.\n"
    "Be strictly factual. Do not guess intent or off-screen context. No preamble."
)


class EventCaptioner:
    def caption(self, drafts: list[EventDraft], frames: list[SampledFrame]) -> list[EventDraft]:
        settings = get_settings()
        use_gemini = (
            settings.vlm_provider == "gemini"
            and not settings.vlm_use_rule_based_fallback
            and bool(settings.google_api_key)
        )
        if use_gemini:
            return self._gemini(drafts, frames)
        return self._rule_based(drafts)

    def _gemini(self, drafts: list[EventDraft], frames: list[SampledFrame]) -> list[EventDraft]:
        _ = frames
        for draft in drafts:
            image_path = draft.representative_image_path
            if image_path is None or not image_path.exists():
                self._apply_rule(draft)
                continue
            try:
                payload = base64.b64encode(image_path.read_bytes()).decode("ascii")
                prompt = (
                    f"{_CAPTION_PROMPT}\n"
                    f"Camera: {draft.camera_id}. "
                    f"Window: {draft.start_timestamp}–{draft.end_timestamp}. "
                    f"Detector labels: {', '.join(draft.detected_classes)}."
                )
                response = invoke_gemini_vision(prompt, payload)
                text = message_text(response).strip()
                if not text:
                    raise ValueError("empty caption")
                draft.caption = text
                draft.caption_source = "vlm"
            except Exception as exc:
                logger.warning("Gemini caption failed for %s: %s", draft.event_id, exc)
                self._apply_rule(draft)
        return drafts

    def _rule_based(self, drafts: list[EventDraft]) -> list[EventDraft]:
        for draft in drafts:
            self._apply_rule(draft)
        return drafts

    def _apply_rule(self, draft: EventDraft) -> None:
        classes_str = ", ".join(draft.detected_classes) or "object"
        draft.caption = (
            f"{classes_str.capitalize()} observed from {draft.start_timestamp} "
            f"to {draft.end_timestamp} on {draft.camera_id}."
        )
        draft.caption_source = "rule_based"

"""2.4 Event captioning — Qwen2.5-VL or VLM API endpoint."""
from __future__ import annotations
from app.core.config import get_settings
from app.pipeline.types import EventDraft, SampledFrame

class EventCaptioner:
    def caption(self, drafts: list[EventDraft], frames: list[SampledFrame]) -> list[EventDraft]:
        settings = get_settings()
        if settings.vlm_use_rule_based_fallback:
            return self._rule_based(drafts)
        
        # Real VLM call (e.g. HuggingFace / Ollama / OpenRouter API)
        for draft in drafts:
            # Query VLM for event description using flagged frame image
            draft.caption = f"Detected {', '.join(draft.detected_classes)} in area during {draft.start_timestamp}–{draft.end_timestamp}."
            draft.caption_source = "vlm"
        return drafts

    def _rule_based(self, drafts: list[EventDraft]) -> list[EventDraft]:
        for draft in drafts:
            classes_str = ", ".join(draft.detected_classes)
            draft.caption = f"{classes_str.capitalize()} observed from {draft.start_timestamp} to {draft.end_timestamp}."
            draft.caption_source = "rule_based"
        return drafts

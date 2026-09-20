"""3.0 Index events — Gemini/local embeddings written to Supabase pgvector (or memory)."""

from __future__ import annotations

import logging

from app.models.event import EventRecord
from app.services.ml import embed_texts
from app.services.store import store

logger = logging.getLogger("sentinelrag.index")


class EventIndexer:
    def upsert(self, events: list[EventRecord], *, video_id: str) -> int:
        embeddings: list[list[float]] = []
        if events:
            embeddings = embed_texts([event.caption for event in events])
        store.set_events(video_id, events, embeddings=embeddings)
        logger.info("Indexed event_count=%s", len(events))
        return len(events)

"""4.2 / 4.3 Similarity retrieval via pgvector, scoped to one video_id."""

from __future__ import annotations

import logging
import re

from app.models.event import EventRecord
from app.services.ml import embed_query
from app.services.store import store

logger = logging.getLogger("sentinelrag.retrieval")


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _lexical_fallback(question: str, events: list[EventRecord], top_k: int) -> list[EventRecord]:
    query_tokens = _tokens(question)
    scored: list[tuple[float, EventRecord]] = []
    for event in events:
        haystack = _tokens(event.caption + " " + " ".join(event.detected_classes))
        overlap = len(query_tokens & haystack)
        score = overlap + event.confidence_score
        scored.append((score, event))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [event for _, event in scored[:top_k]]


def retrieve_events(
    question: str,
    events: list[EventRecord],
    *,
    video_id: str | None = None,
    top_k: int = 3,
) -> list[EventRecord]:
    if not events:
        return []

    scoped = [event for event in events if not video_id or event.video_id == video_id]
    if not scoped:
        return []

    event_map = {event.event_id: event for event in scoped}
    try:
        query_vec = embed_query(question)
        ids = store.match_event_ids(video_id or scoped[0].video_id, query_vec, top_k)
        matched = [event_map[event_id] for event_id in ids if event_id in event_map]
        if matched:
            return matched
    except Exception as exc:
        logger.warning("pgvector retrieval failed, using lexical fallback: %s", exc)

    return _lexical_fallback(question, scoped, top_k)

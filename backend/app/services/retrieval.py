"""4.2 / 4.3 Hybrid retrieval: vector + lexical + class, with a similarity floor."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.event import EventRecord
from app.pipeline.geometry import seconds_from_label
from app.services.embedding_meta import (
    current_embedding_model,
    current_embedding_model_version,
    majority_stored_embedding_model,
    majority_stored_embedding_version,
)
from app.services.ml import embed_query
from app.services.store import store

logger = logging.getLogger("sentinelrag.retrieval")

_STOP = {
    "the",
    "and",
    "for",
    "did",
    "does",
    "anyone",
    "someone",
    "something",
    "this",
    "that",
    "was",
    "were",
    "are",
    "any",
    "how",
    "many",
    "what",
    "when",
    "where",
    "who",
    "with",
    "from",
    "into",
    "onto",
    "near",
    "footage",
    "video",
    "clip",
    "scene",
    "index",
    "please",
    "show",
    "tell",
    "about",
    "there",
    "have",
    "has",
    "been",
    "visible",
    "present",
    "observed",
    "after",
    "before",
    "during",
    "last",
    "first",
}

_CLASS_ALIASES: dict[str, set[str]] = {
    "person": {"person", "people", "man", "woman", "human", "pedestrian", "someone", "anyone"},
    "bicycle": {"bicycle", "bike", "cyclist"},
    "car": {"car", "vehicle", "sedan", "auto"},
    "motorcycle": {"motorcycle", "motorbike", "scooter"},
    "bus": {"bus"},
    "truck": {"truck", "lorry", "vehicle"},
    "backpack": {"backpack", "rucksack", "bag"},
    "handbag": {"handbag", "purse", "bag"},
    "suitcase": {"suitcase", "luggage", "bag"},
    "dog": {"dog", "canine"},
    "cat": {"cat"},
}

_LAST_WINDOW = re.compile(
    r"\blast\s+(\d+(?:\.\d+)?)\s*(seconds?|secs?|s|minutes?|mins?|m)\b",
    re.IGNORECASE,
)
_AFTER = re.compile(r"\bafter\s+(\d{1,2}:\d{2}(?::\d{2})?)\b", re.IGNORECASE)
_BEFORE = re.compile(r"\bbefore\s+(\d{1,2}:\d{2}(?::\d{2})?)\b", re.IGNORECASE)
_BETWEEN = re.compile(
    r"\bbetween\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+and\s+(\d{1,2}:\d{2}(?::\d{2})?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TimeWindow:
    start_seconds: float | None = None
    end_seconds: float | None = None


@dataclass
class RankedEvent:
    event: EventRecord
    vector_sim: float
    lexical: float
    class_hit: float
    score: float


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def _content_tokens(text: str) -> set[str]:
    return {token for token in _tokens(text) if token not in _STOP}


def _is_video_relative_clock(label: str) -> bool:
    """Accept tape-relative clocks only. Ignore wall-clock phrases such as 21:00 or 9:00."""
    parts = label.strip().split(":")
    if len(parts) == 3:
        try:
            return int(parts[0]) == 0 and seconds_from_label(label) is not None
        except ValueError:
            return False
    if len(parts) == 2:
        try:
            return int(parts[0]) == 0 and seconds_from_label(label) is not None
        except ValueError:
            return False
    return False


def parse_time_filter(question: str, events: list[EventRecord]) -> TimeWindow | None:
    last = _LAST_WINDOW.search(question)
    if last:
        amount = float(last.group(1))
        unit = last.group(2).lower()
        span = amount * 60.0 if unit.startswith("m") else amount
        ends = [seconds_from_label(event.end_timestamp) for event in events]
        known = [value for value in ends if value is not None]
        if not known:
            return None
        video_end = max(known)
        return TimeWindow(start_seconds=max(0.0, video_end - span), end_seconds=video_end)

    between = _BETWEEN.search(question)
    if between and _is_video_relative_clock(between.group(1)) and _is_video_relative_clock(between.group(2)):
        start = seconds_from_label(between.group(1))
        end = seconds_from_label(between.group(2))
        if start is None or end is None:
            return None
        return TimeWindow(start_seconds=min(start, end), end_seconds=max(start, end))

    after = _AFTER.search(question)
    if after and _is_video_relative_clock(after.group(1)):
        start = seconds_from_label(after.group(1))
        return TimeWindow(start_seconds=start, end_seconds=None) if start is not None else None

    before = _BEFORE.search(question)
    if before and _is_video_relative_clock(before.group(1)):
        end = seconds_from_label(before.group(1))
        return TimeWindow(start_seconds=None, end_seconds=end) if end is not None else None

    return None


def _event_overlaps_window(event: EventRecord, window: TimeWindow) -> bool:
    start = seconds_from_label(event.start_timestamp)
    end = seconds_from_label(event.end_timestamp)
    if start is None or end is None:
        return True
    if end < start:
        end = start
    if window.start_seconds is not None and end < window.start_seconds:
        return False
    if window.end_seconds is not None and start > window.end_seconds:
        return False
    return True


def _class_hit(question_tokens: set[str], event: EventRecord) -> float:
    for label in event.detected_classes:
        aliases = _CLASS_ALIASES.get(label.lower(), {label.lower()})
        if question_tokens & aliases:
            return 1.0
    caption_tokens = _tokens(event.caption)
    for label, aliases in _CLASS_ALIASES.items():
        if question_tokens & aliases and (label in caption_tokens or aliases & caption_tokens):
            return 1.0
    return 0.0


def _event_search_tokens(event: EventRecord) -> set[str]:
    tokens = _tokens(event.caption) | {cls.lower() for cls in event.detected_classes}
    for label in event.detected_classes:
        tokens |= _CLASS_ALIASES.get(label.lower(), set())
    return tokens


def _lexical_score(query_tokens: set[str], event: EventRecord) -> float:
    if not query_tokens:
        return 0.0
    overlap = query_tokens & _event_search_tokens(event)
    return len(overlap) / max(len(query_tokens), 1)


def _hybrid_score(
    event: EventRecord,
    *,
    query_tokens: set[str],
    raw_tokens: set[str],
    vector_sim: float,
) -> RankedEvent:
    settings = get_settings()
    lexical = _lexical_score(query_tokens, event)
    class_hit = _class_hit(raw_tokens | query_tokens, event)
    score = (
        settings.retrieval_vector_weight * max(0.0, vector_sim)
        + settings.retrieval_lexical_weight * lexical
        + settings.retrieval_class_weight * class_hit
        + settings.retrieval_confidence_weight * event.confidence_score
    )
    return RankedEvent(
        event=event,
        vector_sim=vector_sim,
        lexical=lexical,
        class_hit=class_hit,
        score=score,
    )


def _apply_floor(ranked: list[RankedEvent]) -> list[RankedEvent]:
    if not ranked:
        return []
    settings = get_settings()
    min_sim = settings.retrieval_min_similarity
    has_vector = any(item.vector_sim >= 0.01 for item in ranked)
    kept: list[RankedEvent] = []
    for item in ranked:
        lexical_hit = item.lexical > 0 or item.class_hit > 0
        if has_vector:
            if item.vector_sim >= min_sim or lexical_hit:
                kept.append(item)
        elif lexical_hit:
            kept.append(item)
    return kept


def warn_if_embedding_model_mismatch(events: list[EventRecord]) -> None:
    """Log if the query embedder is not the one that produced most stored vectors."""
    stored_model = majority_stored_embedding_model(events)
    if stored_model is None:
        return
    query_model = current_embedding_model()
    if stored_model != query_model:
        labeled = sum(1 for event in events if event.embedding_model)
        matching = sum(1 for event in events if event.embedding_model == stored_model)
        logger.warning(
            "Query embedding model %r does not match the majority stored model %r "
            "(%s/%s labeled events). Retrieval quality may degrade until the index is rebuilt.",
            query_model,
            stored_model,
            matching,
            labeled,
        )
        return

    stored_version = majority_stored_embedding_version(events, stored_model)
    query_version = current_embedding_model_version()
    if stored_version and query_version and stored_version != query_version:
        logger.warning(
            "Query embedding model %r version %r does not match stored version %r. "
            "Retrieval quality may degrade until the index is rebuilt.",
            query_model,
            query_version,
            stored_version,
        )


def retrieve_events(
    question: str,
    events: list[EventRecord],
    *,
    video_id: str | None = None,
    user_id: str | None = None,
    top_k: int | None = None,
) -> list[EventRecord]:
    if not events:
        return []

    settings = get_settings()
    limit = top_k if top_k is not None else settings.retrieval_top_k
    scoped = [event for event in events if not video_id or event.video_id == video_id]
    if not scoped:
        return []
    warn_if_embedding_model_mismatch(scoped)

    window = parse_time_filter(question, scoped)
    filtered = [event for event in scoped if window is None or _event_overlaps_window(event, window)]
    if not filtered:
        return []

    query_tokens = _content_tokens(question)
    raw_tokens = _tokens(question)
    event_map = {event.event_id: event for event in filtered}
    sim_map: dict[str, float] = {}

    try:
        query_vec = embed_query(question)
        matches = store.match_events(
            video_id or filtered[0].video_id,
            query_vec,
            settings.retrieval_candidate_k,
            user_id=user_id,
        )
        for event_id, similarity in matches:
            if event_id in event_map:
                sim_map[event_id] = float(similarity)
    except Exception as exc:
        logger.warning("Vector retrieval failed, ranking lexically: %s", exc)

    ranked = [
        _hybrid_score(
            event,
            query_tokens=query_tokens,
            raw_tokens=raw_tokens,
            vector_sim=sim_map.get(event.event_id, 0.0),
        )
        for event in filtered
    ]
    ranked.sort(key=lambda item: (item.score, item.vector_sim, item.event.confidence_score), reverse=True)
    kept = _apply_floor(ranked)
    return [item.event for item in kept[:limit]]

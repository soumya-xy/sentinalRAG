"""Embedding identity for writes and retrieval checks. Always read from settings."""

from __future__ import annotations

from collections import Counter

from app.core.config import get_settings
from app.models.event import EventRecord


def current_embedding_model() -> str:
    return get_settings().active_embedding_model


def current_embedding_model_version() -> str | None:
    return get_settings().active_embedding_model_version


def stamp_events(events: list[EventRecord]) -> list[EventRecord]:
    model = current_embedding_model()
    version = current_embedding_model_version()
    return [
        event.model_copy(
            update={
                "embedding_model": model,
                "embedding_model_version": version,
            }
        )
        for event in events
    ]


def majority_stored_embedding_model(events: list[EventRecord]) -> str | None:
    labeled = [event.embedding_model for event in events if event.embedding_model]
    if not labeled:
        return None
    counts = Counter(labeled)
    return counts.most_common(1)[0][0]


def majority_stored_embedding_version(events: list[EventRecord], model: str) -> str | None:
    labeled = [
        event.embedding_model_version
        for event in events
        if event.embedding_model == model and event.embedding_model_version
    ]
    if not labeled:
        return None
    return Counter(labeled).most_common(1)[0][0]

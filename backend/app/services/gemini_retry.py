"""Shared exponential backoff for transient Gemini / HTTP failures."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from app.core.config import get_settings
from app.core.context import get_query_id, get_video_id

logger = logging.getLogger("sentinelrag.retry")

T = TypeVar("T")

_TRANSIENT_STATUS = {408, 429, 500, 502, 503, 504}
_TRANSIENT_NAMES = {
    "aborted",
    "deadlineexceeded",
    "internal",
    "internalservererror",
    "resourceexhausted",
    "serviceunavailable",
    "toomanyrequests",
    "unavailable",
}


def _iter_exceptions(exc: BaseException):
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _status_code(exc: BaseException) -> int | None:
    for attr in ("status_code", "http_status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int) and value > 0:
            if attr == "code" and value < 100:
                continue
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return code
    return None


def is_transient_error(exc: BaseException) -> bool:
    """True for rate limits and 5xx-class transport failures, including wrapped causes."""
    for item in _iter_exceptions(exc):
        status = _status_code(item)
        if status in _TRANSIENT_STATUS:
            return True
        name = type(item).__name__.lower().replace("_", "")
        if name in _TRANSIENT_NAMES:
            return True
        message = str(item).lower()
        if "429" in message or "resource exhausted" in message or "rate limit" in message:
            return True
        if "503" in message or "unavailable" in message:
            return True
    return False


def _context(*, video_id: str | None, query_id: str | None, event_id: str | None) -> str:
    parts = []
    if video_id:
        parts.append(f"video_id={video_id}")
    if query_id:
        parts.append(f"query_id={query_id}")
    if event_id:
        parts.append(f"event_id={event_id}")
    return " ".join(parts) if parts else "video_id=- query_id=-"


def call_with_backoff(
    operation: Callable[[], T],
    *,
    stage: str,
    video_id: str | None = None,
    query_id: str | None = None,
    event_id: str | None = None,
    attempts: int | None = None,
    base_delay: float | None = None,
) -> T:
    settings = get_settings()
    max_attempts = attempts if attempts is not None else settings.gemini_retry_attempts
    delay_base = (
        base_delay if base_delay is not None else settings.gemini_retry_base_delay_seconds
    )
    max_attempts = max(1, max_attempts)
    video_id = video_id or get_video_id()
    query_id = query_id or get_query_id()
    ctx = _context(video_id=video_id, query_id=query_id, event_id=event_id)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            retryable = is_transient_error(exc) and attempt < max_attempts
            if not retryable:
                raise
            delay = delay_base * (2 ** (attempt - 1))
            logger.warning(
                "Retry %s/%s for %s after transient error (%.1fs). %s err=%s",
                attempt,
                max_attempts,
                stage,
                delay,
                ctx,
                exc,
            )
            time.sleep(delay)

    assert last_error is not None
    raise last_error

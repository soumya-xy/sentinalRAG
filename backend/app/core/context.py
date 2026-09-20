"""Request-scoped IDs for structured logs. Set by middleware / entry points, not passed down."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_video_id: ContextVar[str | None] = ContextVar("video_id", default=None)
_query_id: ContextVar[str | None] = ContextVar("query_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def get_video_id() -> str | None:
    return _video_id.get()


def get_query_id() -> str | None:
    return _query_id.get()


def set_request_id(value: str | None) -> None:
    _request_id.set(value)


def set_video_id(value: str | None) -> None:
    _video_id.set(value)


def set_query_id(value: str | None) -> None:
    _query_id.set(value)


@contextmanager
def bind_log_context(
    *,
    request_id: str | None = None,
    video_id: str | None = None,
    query_id: str | None = None,
) -> Iterator[None]:
    tokens: list[tuple[ContextVar[str | None], Token]] = []
    if request_id is not None:
        tokens.append((_request_id, _request_id.set(request_id)))
    if video_id is not None:
        tokens.append((_video_id, _video_id.set(video_id)))
    if query_id is not None:
        tokens.append((_query_id, _query_id.set(query_id)))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)

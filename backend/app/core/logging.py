"""Structured logging: JSON lines plus contextvars (request_id, video_id, query_id)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

from app.core.config import get_settings
from app.core.context import get_query_id, get_request_id, get_video_id

_HANDLER_MARK = "_sentinelrag_handler"
_previous_factory: Callable[..., logging.LogRecord] | None = None


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "video_id": getattr(record, "video_id", "-"),
            "query_id": getattr(record, "query_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(
            "%(asctime)s %(levelname)s %(name)s "
            "request_id=%(request_id)s video_id=%(video_id)s query_id=%(query_id)s "
            "%(message)s"
        )


def _record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
    factory = _previous_factory or logging.LogRecord
    record = factory(*args, **kwargs)
    record.request_id = get_request_id() or "-"
    record.video_id = get_video_id() or "-"
    record.query_id = get_query_id() or "-"
    return record


def configure_logging() -> None:
    global _previous_factory
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    current = logging.getLogRecordFactory()
    if current is not _record_factory:
        _previous_factory = current
        logging.setLogRecordFactory(_record_factory)

    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(handler, _HANDLER_MARK, False) for handler in root.handlers):
        handler = logging.StreamHandler()
        setattr(handler, _HANDLER_MARK, True)
        if (settings.log_format or "json").lower() == "text":
            handler.setFormatter(TextFormatter())
        else:
            handler.setFormatter(JsonFormatter())
        root.addHandler(handler)

    logging.getLogger("sentinelrag").setLevel(level)

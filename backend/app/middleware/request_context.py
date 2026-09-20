"""Attach a request-scoped correlation ID. Reused as query_id on /api/query."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import bind_log_context, get_query_id, get_request_id


def new_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def incoming_request_id(request: Request) -> str:
    for header in ("x-request-id", "x-correlation-id"):
        value = request.headers.get(header)
        if value and value.strip():
            return value.strip()
    return new_request_id()


def video_id_from_path(path: str) -> str | None:
    parts = [item for item in path.split("/") if item]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "videos":
        candidate = parts[2]
        if candidate.startswith("vid_"):
            return candidate
    return None


def is_query_path(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    return normalized == "/api/query"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = incoming_request_id(request)
        query_id = request_id if is_query_path(request.url.path) else None
        video_id = video_id_from_path(request.url.path)
        with bind_log_context(request_id=request_id, query_id=query_id, video_id=video_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = get_request_id() or request_id
            current_query = get_query_id()
            if current_query:
                response.headers["X-Query-ID"] = current_query
            return response

"""Supabase Storage helpers. Nothing is written to the project data/ folder."""

from __future__ import annotations

import base64
import re
from pathlib import Path

from app.core.config import get_settings
from app.models.event import EventRecord
from app.services.supabase_client import get_admin_client, reset_supabase_clients


def video_object_key(user_id: str, video_id: str, suffix: str) -> str:
    safe = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{user_id}/{video_id}{safe}"


def thumbnail_object_key(user_id: str, video_id: str, filename: str) -> str:
    return f"{user_id}/{video_id}/{filename}"


def upload_bytes(bucket: str, key: str, data: bytes, content_type: str) -> str:
    try:
        client = get_admin_client()
        client.storage.from_(bucket).upload(
            key,
            data,
            {"content-type": content_type, "upsert": "true"},
        )
        return key
    except Exception as exc:
        reset_supabase_clients()
        err_str = str(exc)
        if "10035" in err_str or "socket" in err_str.lower() or "winerror" in err_str.lower():
            # Retry once with a fresh client and new connection pool
            client = get_admin_client()
            client.storage.from_(bucket).upload(
                key,
                data,
                {"content-type": content_type, "upsert": "true"},
            )
            return key
        raise


def upload_video(user_id: str, video_id: str, suffix: str, data: bytes, content_type: str) -> str:
    settings = get_settings()
    key = video_object_key(user_id, video_id, suffix)
    return upload_bytes(settings.supabase_videos_bucket, key, data, content_type)


def download_object(bucket: str, key: str) -> bytes:
    try:
        client = get_admin_client()
        payload = client.storage.from_(bucket).download(key)
        if isinstance(payload, bytes):
            return payload
        return bytes(payload)
    except Exception:
        reset_supabase_clients()
        raise


def download_video_to(key: str, dest: Path) -> Path:
    settings = get_settings()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(download_object(settings.supabase_videos_bucket, key))
    return dest


def upload_thumbnail(
    user_id: str,
    video_id: str,
    event_id: str,
    data: bytes,
    *,
    suffix: str = ".jpg",
    content_type: str = "image/jpeg",
) -> str:
    settings = get_settings()
    safe = suffix if suffix.startswith(".") else f".{suffix}"
    key = thumbnail_object_key(user_id, video_id, f"{event_id}{safe}")
    return upload_bytes(settings.supabase_thumbnails_bucket, key, data, content_type)


def download_thumbnail(key: str) -> bytes:
    settings = get_settings()
    return download_object(settings.supabase_thumbnails_bucket, key)


def _absolute_signed_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    base = get_settings().supabase_url.rstrip("/")
    return f"{base}{url if url.startswith('/') else f'/{url}'}"


def _signed_url_from_payload(payload: object) -> str | None:
    if isinstance(payload, str) and payload:
        return _absolute_signed_url(payload)
    if not isinstance(payload, dict):
        return None
    for key in ("signedURL", "signedUrl", "signed_url"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return _absolute_signed_url(value)
    return None


def signed_thumbnail_url(key: str, expires_in: int | None = None) -> str | None:
    """Mint a time-limited Storage URL. Never persist this on the event row."""
    if not key or looks_like_inline_image(key):
        return None
    settings = get_settings()
    ttl = expires_in if expires_in is not None else settings.thumbnail_signed_url_ttl_seconds
    try:
        client = get_admin_client()
        payload = client.storage.from_(settings.supabase_thumbnails_bucket).create_signed_url(
            key,
            ttl,
        )
        return _signed_url_from_payload(payload)
    except Exception:
        reset_supabase_clients()
        return None


def sign_thumbnail_urls(keys: list[str], expires_in: int | None = None) -> dict[str, str]:
    unique = [key for key in dict.fromkeys(keys) if key and not looks_like_inline_image(key)]
    if not unique:
        return {}
    settings = get_settings()
    ttl = expires_in if expires_in is not None else settings.thumbnail_signed_url_ttl_seconds
    signed: dict[str, str] = {}
    try:
        client = get_admin_client()
        payload = client.storage.from_(settings.supabase_thumbnails_bucket).create_signed_urls(
            unique,
            ttl,
        )
        rows = payload if isinstance(payload, list) else []
        for row in rows:
            if not isinstance(row, dict) or row.get("error"):
                continue
            path = str(row.get("path") or row.get("name") or "")
            url = _signed_url_from_payload(row)
            if path and url:
                signed[path] = url
    except Exception:
        reset_supabase_clients()
    for key in unique:
        if key not in signed:
            url = signed_thumbnail_url(key, expires_in=ttl)
            if url:
                signed[key] = url
    return signed


_INLINE_B64_RE = re.compile(r"^[A-Za-z0-9+/=\n\r]+$")


def looks_like_inline_image(value: str | None) -> bool:
    if not value:
        return False
    stripped = value.strip()
    if stripped.startswith("data:image"):
        return True
    if "base64," in stripped[:80]:
        return True
    # Raw base64 leftovers: long, no path punctuation, JPEG/PNG alphabet only.
    if len(stripped) >= 400 and _INLINE_B64_RE.match(stripped):
        return True
    return False


def decode_inline_image(value: str) -> tuple[bytes, str, str]:
    payload = value.strip()
    content_type = "image/jpeg"
    suffix = ".jpg"
    if payload.startswith("data:"):
        header, _, payload = payload.partition(",")
        meta = header[5:] if header.startswith("data:") else header
        ctype = meta.split(";", 1)[0] or "image/jpeg"
        content_type = ctype
        if "png" in ctype:
            suffix = ".png"
        elif "svg" in ctype:
            suffix = ".svg"
            content_type = "image/svg+xml"
        elif "webp" in ctype:
            suffix = ".webp"
    raw = base64.b64decode(payload, validate=False)
    if not raw:
        raise ValueError("empty inline thumbnail")
    return raw, suffix, content_type


def media_fallback_url(video_id: str, storage_key: str) -> str:
    filename = Path(storage_key).name or storage_key
    return f"/api/media/{video_id}/{filename}"


def _is_http_url(value: str | None) -> bool:
    return bool(value and (value.startswith("http://") or value.startswith("https://")))


def attach_signed_thumbnail_urls(events: list[EventRecord]) -> list[EventRecord]:
    """Fill `thumbnail_url` with a 1-hour signed Storage URL for API responses.

    The signed URL is never written back to Postgres.
    """
    settings = get_settings()
    keys: list[str] = []
    if settings.supabase_enabled:
        keys = [
            event.thumbnail_path
            for event in events
            if event.thumbnail_path
            and not looks_like_inline_image(event.thumbnail_path)
            and not _is_http_url(event.thumbnail_url)
        ]
    signed = sign_thumbnail_urls(keys) if keys else {}
    attached: list[EventRecord] = []
    for event in events:
        if _is_http_url(event.thumbnail_url):
            attached.append(event)
            continue
        url = signed.get(event.thumbnail_path)
        if not url and event.thumbnail_path and not looks_like_inline_image(event.thumbnail_path):
            url = media_fallback_url(event.video_id, event.thumbnail_path)
        attached.append(event.model_copy(update={"thumbnail_url": url}))
    return attached

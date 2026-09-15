"""Supabase Storage helpers. Nothing is written to the project data/ folder."""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.services.supabase_client import get_admin_client


def video_object_key(user_id: str, video_id: str, suffix: str) -> str:
    safe = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{user_id}/{video_id}{safe}"


def thumbnail_object_key(user_id: str, video_id: str, filename: str) -> str:
    return f"{user_id}/{video_id}/{filename}"


def upload_bytes(bucket: str, key: str, data: bytes, content_type: str) -> str:
    client = get_admin_client()
    client.storage.from_(bucket).upload(
        key,
        data,
        {"content-type": content_type, "upsert": "true"},
    )
    return key


def upload_video(user_id: str, video_id: str, suffix: str, data: bytes, content_type: str) -> str:
    settings = get_settings()
    key = video_object_key(user_id, video_id, suffix)
    return upload_bytes(settings.supabase_videos_bucket, key, data, content_type)


def download_object(bucket: str, key: str) -> bytes:
    client = get_admin_client()
    payload = client.storage.from_(bucket).download(key)
    if isinstance(payload, bytes):
        return payload
    return bytes(payload)


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

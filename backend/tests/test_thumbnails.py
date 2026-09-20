import base64
from collections.abc import Generator

import pytest

from app.core.config import reset_settings_cache
from app.models.event import BoundingBox, EventRecord
from app.services.object_storage import (
    attach_signed_thumbnail_urls,
    decode_inline_image,
    looks_like_inline_image,
    media_fallback_url,
)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Generator[None, None, None]:
    reset_settings_cache()
    yield
    reset_settings_cache()


def _event(**overrides: object) -> EventRecord:
    payload = {
        "event_id": "evt_1",
        "video_id": "vid_1",
        "camera_id": "cam-01",
        "start_timestamp": "00:00:01",
        "end_timestamp": "00:00:04",
        "caption": "person standing",
        "detected_classes": ["person"],
        "bounding_boxes": [BoundingBox(x=1, y=1, w=10, h=10, frame_timestamp="00:00:02")],
        "thumbnail_path": "user/vid_1/evt_1.jpg",
        "confidence_score": 0.9,
    }
    payload.update(overrides)
    return EventRecord.model_validate(payload)


def test_looks_like_inline_image_detects_data_uri_and_raw_base64() -> None:
    tiny = base64.b64encode(b"\xff\xd8\xff" + b"x" * 80).decode("ascii")
    assert looks_like_inline_image(f"data:image/jpeg;base64,{tiny}")
    assert looks_like_inline_image("data:image/png;base64,iVBORw0KGgo=")
    assert looks_like_inline_image(tiny * 8)
    assert not looks_like_inline_image("user/vid_1/evt_1.jpg")
    assert not looks_like_inline_image("/api/media/vid_1/evt_1.jpg")
    assert not looks_like_inline_image(None)


def test_decode_inline_image_reads_data_uri() -> None:
    raw = b"\xff\xd8\xff" + b"jpeg-bytes"
    encoded = base64.b64encode(raw).decode("ascii")
    data, suffix, content_type = decode_inline_image(f"data:image/jpeg;base64,{encoded}")
    assert data == raw
    assert suffix == ".jpg"
    assert content_type == "image/jpeg"


def test_attach_signed_urls_falls_back_to_media_path_without_supabase(
    monkeypatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    reset_settings_cache()
    attached = attach_signed_thumbnail_urls([_event(thumbnail_url=None)])
    assert attached[0].thumbnail_path == "user/vid_1/evt_1.jpg"
    assert attached[0].thumbnail_url == "/api/media/vid_1/evt_1.jpg"


def test_attach_signed_urls_mints_storage_url(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    reset_settings_cache()
    monkeypatch.setattr(
        "app.services.object_storage.sign_thumbnail_urls",
        lambda keys, expires_in=None: {
            keys[0]: "https://example.supabase.co/storage/v1/object/sign/thumbnails/user/vid_1/evt_1.jpg?token=abc"
        },
    )
    attached = attach_signed_thumbnail_urls([_event(thumbnail_url=None)])
    assert attached[0].thumbnail_url.startswith("https://example.supabase.co/storage/")
    assert "token=" in attached[0].thumbnail_url


def test_media_fallback_url_uses_filename_only() -> None:
    assert media_fallback_url("vid_1", "usr/vid_1/evt_1.jpg") == "/api/media/vid_1/evt_1.jpg"

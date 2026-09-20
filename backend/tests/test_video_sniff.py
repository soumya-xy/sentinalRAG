import pytest

from app.services.video_sniff import VideoSniffError, sniff_payload, validate_video_payload
from tests.fakes import fake_avi_bytes, fake_jpeg_bytes, fake_mp4_bytes


def test_sniff_mp4_ftyp() -> None:
    result = sniff_payload(fake_mp4_bytes())
    assert result is not None
    assert result.kind == "mp4"


def test_sniff_quicktime_brand() -> None:
    header = bytearray(32)
    header[4:8] = b"ftyp"
    header[8:12] = b"qt  "
    result = sniff_payload(bytes(header))
    assert result is not None
    assert result.kind == "mov"


def test_sniff_avi_and_jpeg() -> None:
    assert sniff_payload(fake_avi_bytes()).kind == "avi"
    assert sniff_payload(fake_jpeg_bytes()).kind == "jpeg"
    assert sniff_payload(b"short") is None


def test_validate_accepts_matching_mp4() -> None:
    sniffed = validate_video_payload(fake_mp4_bytes(), ".mp4")
    assert sniffed.kind == "mp4"


def test_validate_rejects_jpeg_named_mp4() -> None:
    with pytest.raises(VideoSniffError, match="JPEG image"):
        validate_video_payload(fake_jpeg_bytes(), ".mp4")


def test_validate_rejects_mp4_named_avi() -> None:
    with pytest.raises(VideoSniffError, match=r"\.avi"):
        validate_video_payload(fake_mp4_bytes(), ".avi")


def test_validate_allows_iso_family_as_mov() -> None:
    sniffed = validate_video_payload(fake_mp4_bytes(), ".mov")
    assert sniffed.kind == "mp4"
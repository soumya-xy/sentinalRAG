"""Magic-byte sniffing for uploaded video containers.

Does not trust the filename or the client Content-Type header.
python-magic is avoided because it needs a native libmagic on Windows.
"""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

# ISO BMFF variants (.mp4 / .m4v / .mov) share the same box format.
# Distinct containers (AVI, MKV, WebM) must match the declared suffix.
_ISO_FAMILY = frozenset({"mp4", "m4v", "mov"})
_ALLOWED_KINDS = {
    ".mp4": _ISO_FAMILY,
    ".m4v": _ISO_FAMILY,
    ".mov": _ISO_FAMILY,
    ".avi": frozenset({"avi"}),
    ".mkv": frozenset({"mkv"}),
    ".webm": frozenset({"webm"}),
}

_KIND_LABELS = {
    "mp4": "MP4",
    "m4v": "M4V",
    "mov": "QuickTime MOV",
    "avi": "AVI",
    "mkv": "Matroska (MKV)",
    "webm": "WebM",
    "jpeg": "JPEG image",
    "png": "PNG image",
    "gif": "GIF image",
    "webp": "WebP image",
    "pdf": "PDF document",
    "zip": "ZIP archive",
}

_MP4_BRANDS = {
    b"isom",
    b"iso2",
    b"iso3",
    b"iso4",
    b"iso5",
    b"iso6",
    b"mp41",
    b"mp42",
    b"mp71",
    b"avc1",
    b"dash",
    b"msdh",
    b"mmp4",
    b"mp4v",
}
_M4V_BRANDS = {b"M4V ", b"M4VH", b"M4VP"}
_QT_ATOMS = {b"moov", b"mdat", b"wide", b"free", b"skip", b"pnot"}


class VideoSniffError(ValueError):
    """Safe, user-facing validation failure. Never include a traceback."""


@dataclass(frozen=True)
class SniffResult:
    kind: str
    label: str


def sniff_payload(payload: bytes) -> SniffResult | None:
    if len(payload) < 12:
        return None
    head = payload[:4096]

    if head.startswith(b"\xff\xd8\xff"):
        return SniffResult("jpeg", _KIND_LABELS["jpeg"])
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return SniffResult("png", _KIND_LABELS["png"])
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return SniffResult("gif", _KIND_LABELS["gif"])
    if head.startswith(b"%PDF"):
        return SniffResult("pdf", _KIND_LABELS["pdf"])
    if head.startswith(b"PK\x03\x04") or head.startswith(b"PK\x05\x06"):
        return SniffResult("zip", _KIND_LABELS["zip"])
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return SniffResult("webp", _KIND_LABELS["webp"])

    if head.startswith(b"RIFF") and head[8:12] in {b"AVI ", b"AVIX"}:
        return SniffResult("avi", _KIND_LABELS["avi"])

    if head.startswith(b"\x1a\x45\xdf\xa3"):
        lowered = head.lower()
        if b"webm" in lowered:
            return SniffResult("webm", _KIND_LABELS["webm"])
        return SniffResult("mkv", _KIND_LABELS["mkv"])

    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand == b"qt  ":
            return SniffResult("mov", _KIND_LABELS["mov"])
        if brand in _M4V_BRANDS:
            return SniffResult("m4v", _KIND_LABELS["m4v"])
        if brand in _MP4_BRANDS or brand[:3] == b"mp4":
            return SniffResult("mp4", _KIND_LABELS["mp4"])
        # Unknown ISO brand is still an ISO Base Media / MP4-family file.
        return SniffResult("mp4", _KIND_LABELS["mp4"])

    if len(head) >= 8 and head[4:8] in _QT_ATOMS:
        return SniffResult("mov", _KIND_LABELS["mov"])

    return None


def validate_video_payload(payload: bytes, suffix: str) -> SniffResult:
    """Confirm bytes are a video container that matches `suffix` (e.g. '.mp4')."""
    suffix = (suffix or "").lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
        raise VideoSniffError(f"Unsupported video type. Use one of: {allowed}")

    sniffed = sniff_payload(payload)
    allowed_kinds = _ALLOWED_KINDS[suffix]
    if sniffed is None:
        raise VideoSniffError(
            f"Could not recognize a video container from the file contents. "
            f"Expected a valid video matching the {suffix} extension "
            f"(MP4, MOV, MKV, AVI, or WebM)."
        )
    if sniffed.kind not in allowed_kinds:
        if sniffed.kind in _KIND_LABELS and sniffed.kind not in {
            "mp4",
            "m4v",
            "mov",
            "avi",
            "mkv",
            "webm",
        }:
            raise VideoSniffError(
                f"File contents are a {sniffed.label}, not a video. "
                f"The {suffix} extension does not match the file signature."
            )
        raise VideoSniffError(
            f"The file extension is {suffix} but the contents are {sniffed.label}. "
            f"Rename the file to match its actual type or upload a real {suffix[1:].upper()}."
        )
    return sniffed

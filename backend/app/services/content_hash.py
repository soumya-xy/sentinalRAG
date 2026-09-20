"""SHA-256 of uploaded video bytes. Stored on the video row for dedup."""

from __future__ import annotations

import hashlib


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

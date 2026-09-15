from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """Stub password hash. TODO: replace with passlib/bcrypt for a real deploy."""
    secret = get_settings().jwt_secret
    return sha256(f"{secret}:{password}".encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_access_token(*, subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expiry_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired token") from exc

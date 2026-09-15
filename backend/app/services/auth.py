from uuid import uuid4

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.auth import AuthResponse, UserPublic
from app.services.catalog_types import UserRecord
from app.services.store import store
from app.services.supabase_client import get_anon_client


def to_public(user: UserRecord) -> UserPublic:
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
    )


def user_from_supabase(payload) -> UserRecord:
    metadata = payload.user_metadata or {}
    display = (
        metadata.get("display_name")
        or metadata.get("full_name")
        or (payload.email or "operator").split("@", 1)[0]
    )
    return UserRecord(
        user_id=str(payload.id),
        email=str(payload.email or ""),
        display_name=str(display),
    )


def issue_auth(user: UserRecord) -> AuthResponse:
    token = create_access_token(subject=user.user_id, extra={"email": user.email})
    return AuthResponse(access_token=token, user=to_public(user))


def register_user(*, email: str, password: str, display_name: str) -> AuthResponse:
    name = display_name.strip() or email.split("@", 1)[0]
    if get_settings().supabase_enabled:
        client = get_anon_client()
        try:
            result = client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"display_name": name}},
                }
            )
        except Exception as exc:
            message = str(exc)
            if "already" in message.lower() or "registered" in message.lower():
                raise ValueError("An account with this email already exists") from exc
            raise ValueError(message) from exc
        if result.user is None:
            raise ValueError("Registration failed")
        if result.session is None or not result.session.access_token:
            raise ValueError(
                "Account created but email confirmation is enabled. "
                "In Supabase Auth settings, turn off 'Confirm email' for local development."
            )
        user = user_from_supabase(result.user)
        return AuthResponse(access_token=result.session.access_token, user=to_public(user))

    user = store.create_user(
        user_id=f"usr_{uuid4().hex[:10]}",
        email=email,
        display_name=name,
        password=password,
    )
    return issue_auth(user)


def login_user(*, email: str, password: str) -> AuthResponse:
    if get_settings().supabase_enabled:
        client = get_anon_client()
        try:
            result = client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as exc:
            raise ValueError("Invalid email or password") from exc
        if result.user is None or result.session is None or not result.session.access_token:
            raise ValueError("Invalid email or password")
        user = user_from_supabase(result.user)
        return AuthResponse(access_token=result.session.access_token, user=to_public(user))

    user = store.get_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return issue_auth(user)


def logout_user(token: str) -> None:
    if get_settings().supabase_enabled:
        return
    store.revoke_token(token)


def resolve_user_from_token(token: str) -> UserRecord:
    settings = get_settings()
    if settings.supabase_enabled:
        try:
            result = get_anon_client().auth.get_user(token)
        except Exception as exc:
            raise ValueError("Invalid or expired token") from exc
        if result.user is None:
            raise ValueError("Invalid or expired token")
        return user_from_supabase(result.user)

    if store.is_revoked(token):
        raise ValueError("Session expired")
    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token")
    user = store.get_user(user_id)
    if user is None:
        raise ValueError("User not found")
    return user

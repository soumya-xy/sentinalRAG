from uuid import uuid4

from app.core.security import create_access_token, verify_password
from app.models.auth import AuthResponse, UserPublic
from app.services.store import UserRecord, store


def to_public(user: UserRecord) -> UserPublic:
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
    )


def issue_auth(user: UserRecord) -> AuthResponse:
    token = create_access_token(subject=user.user_id, extra={"email": user.email})
    return AuthResponse(access_token=token, user=to_public(user))


def register_user(*, email: str, password: str, display_name: str) -> AuthResponse:
    name = display_name.strip() or email.split("@", 1)[0]
    user = store.create_user(
        user_id=f"usr_{uuid4().hex[:10]}",
        email=email,
        display_name=name,
        password=password,
    )
    return issue_auth(user)


def login_user(*, email: str, password: str) -> AuthResponse:
    user = store.get_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return issue_auth(user)


def logout_user(token: str) -> None:
    store.revoke_token(token)

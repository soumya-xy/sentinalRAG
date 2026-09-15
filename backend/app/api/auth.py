from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_bearer_token, get_current_user
from app.models.auth import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.models.common import OkResponse
from app.services.auth import login_user, logout_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest) -> AuthResponse:
    try:
        return register_user(
            email=str(body.email),
            password=body.password,
            display_name=body.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    try:
        return login_user(email=str(body.email), password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout", response_model=OkResponse)
def logout(token: str = Depends(get_bearer_token)) -> OkResponse:
    logout_user(token)
    return OkResponse(ok=True)


@router.get("/me", response_model=UserPublic)
def me(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return user

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from app.core.security import hash_password
from app.models.event import EventRecord
from app.models.video import VideoStatus


@dataclass
class UserRecord:
    user_id: str
    email: str
    display_name: str
    password_hash: str


@dataclass
class VideoInternal:
    video_id: str
    user_id: str
    camera_id: str
    filename: str
    original_filename: str
    stored_path: str
    status: VideoStatus
    created_at: datetime
    size_bytes: int
    duration_seconds: float | None = 1020.0
    error: str | None = None
    events_materialized: bool = False


@dataclass
class AppStore:
    users_by_id: dict[str, UserRecord] = field(default_factory=dict)
    users_by_email: dict[str, str] = field(default_factory=dict)
    revoked_tokens: set[str] = field(default_factory=set)
    videos: dict[str, VideoInternal] = field(default_factory=dict)
    events_by_video: dict[str, list[EventRecord]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def clear(self) -> None:
        with self._lock:
            self.users_by_id.clear()
            self.users_by_email.clear()
            self.revoked_tokens.clear()
            self.videos.clear()
            self.events_by_video.clear()

    def seed_demo_user(self) -> UserRecord:
        existing = self.get_user_by_email("demo@sentinelrag.dev")
        if existing:
            return existing
        return self.create_user(
            user_id="usr_demo",
            email="demo@sentinelrag.dev",
            display_name="Demo operator",
            password="demo1234",
        )

    def create_user(self, *, user_id: str, email: str, display_name: str, password: str) -> UserRecord:
        with self._lock:
            if email.lower() in self.users_by_email:
                raise ValueError("An account with this email already exists")
            record = UserRecord(
                user_id=user_id,
                email=email.lower(),
                display_name=display_name,
                password_hash=hash_password(password),
            )
            self.users_by_id[user_id] = record
            self.users_by_email[record.email] = user_id
            return record

    def get_user(self, user_id: str) -> UserRecord | None:
        return self.users_by_id.get(user_id)

    def get_user_by_email(self, email: str) -> UserRecord | None:
        user_id = self.users_by_email.get(email.lower())
        if not user_id:
            return None
        return self.users_by_id.get(user_id)

    def revoke_token(self, token: str) -> None:
        with self._lock:
            self.revoked_tokens.add(token)

    def is_revoked(self, token: str) -> bool:
        return token in self.revoked_tokens

    def put_video(self, video: VideoInternal) -> VideoInternal:
        with self._lock:
            self.videos[video.video_id] = video
            return video

    def get_video(self, video_id: str) -> VideoInternal | None:
        return self.videos.get(video_id)

    def list_videos(self, user_id: str) -> list[VideoInternal]:
        items = [video for video in self.videos.values() if video.user_id == user_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def set_video_status(
        self,
        video_id: str,
        status: VideoStatus,
        error: str | None = None,
    ) -> None:
        with self._lock:
            video = self.videos.get(video_id)
            if video is None:
                return
            video.status = status
            video.error = error

    def set_events(self, video_id: str, events: list[EventRecord]) -> None:
        with self._lock:
            self.events_by_video[video_id] = events
            video = self.videos.get(video_id)
            if video:
                video.events_materialized = True
                video.status = "ready"

    def get_events(self, video_id: str) -> list[EventRecord]:
        return list(self.events_by_video.get(video_id, []))


store = AppStore()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


CaptionMode = Literal["vlm", "rule_based"]

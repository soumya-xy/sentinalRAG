"""In-memory catalog used only when Supabase is not configured (pytest)."""

from __future__ import annotations

from threading import Lock

from app.core.security import hash_password
from app.models.event import EventRecord
from app.models.video import VideoStatus
from app.services.catalog_types import STAGE_KEYS, UserRecord, VideoInternal


class MemoryCatalog:
    def __init__(self) -> None:
        self.users_by_id: dict[str, UserRecord] = {}
        self.users_by_email: dict[str, str] = {}
        self.revoked_tokens: set[str] = set()
        self.videos: dict[str, VideoInternal] = {}
        self.events_by_video: dict[str, list[EventRecord]] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self.users_by_id.clear()
            self.users_by_email.clear()
            self.revoked_tokens.clear()
            self.videos.clear()
            self.events_by_video.clear()

    def load(self) -> None:
        return

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

    def begin_pipeline(self, video_id: str) -> None:
        with self._lock:
            video = self.videos.get(video_id)
            if video is None:
                return
            video.status = "processing"
            video.error = None
            video.events_materialized = False
            video.current_stage = "ingest"
            video.stage_states = {key: "pending" for key in STAGE_KEYS}
            video.stage_progress = {key: 0.0 for key in STAGE_KEYS}
            video.stage_states["ingest"] = "complete"
            video.stage_progress["ingest"] = 100.0
            video.overall_progress = 100.0 / len(STAGE_KEYS)

    def update_stage(self, video_id: str, key: str, progress: float, state: str) -> None:
        with self._lock:
            video = self.videos.get(video_id)
            if video is None or key not in video.stage_states:
                return
            index = STAGE_KEYS.index(key)
            for prior in STAGE_KEYS[:index]:
                video.stage_states[prior] = "complete"
                video.stage_progress[prior] = 100.0
            video.stage_states[key] = state
            video.stage_progress[key] = max(0.0, min(100.0, progress))
            video.current_stage = key
            if state == "complete" and key == STAGE_KEYS[-1]:
                video.status = "ready"
                video.events_materialized = True
            elif not video.events_materialized:
                video.status = "processing"
            completed = index + 1 if state == "complete" else index
            running = 0.0 if state == "complete" else video.stage_progress[key] / 100.0
            video.overall_progress = round(((completed + running) / len(STAGE_KEYS)) * 100.0, 1)

    def fail_pipeline(self, video_id: str, error: str, failed_key: str | None = None) -> None:
        with self._lock:
            video = self.videos.get(video_id)
            if video is None:
                return
            video.status = "failed"
            video.error = error
            key = failed_key or video.current_stage or "ingest"
            if key in video.stage_states:
                video.stage_states[key] = "failed"
            video.current_stage = key

    def set_events(
        self,
        video_id: str,
        events: list[EventRecord],
        embeddings: list[list[float]] | None = None,
    ) -> None:
        _ = embeddings
        with self._lock:
            self.events_by_video[video_id] = events
            video = self.videos.get(video_id)
            if video:
                video.events_materialized = True
                video.status = "ready"
                video.error = None
                video.current_stage = None
                video.overall_progress = 100.0
                for key in STAGE_KEYS:
                    video.stage_states[key] = "complete"
                    video.stage_progress[key] = 100.0

    def get_events(self, video_id: str) -> list[EventRecord]:
        return list(self.events_by_video.get(video_id, []))

    def match_event_ids(self, video_id: str, query_embedding: list[float], top_k: int) -> list[str]:
        _ = query_embedding
        return [event.event_id for event in self.get_events(video_id)[:top_k]]

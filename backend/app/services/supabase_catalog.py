"""Video/event catalog on Supabase Postgres + pgvector."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.event import EventRecord
from app.models.video import VideoStatus
from app.services.catalog_types import STAGE_KEYS, VideoInternal
from app.services.embedding_meta import current_embedding_model, current_embedding_model_version
from app.services.supabase_client import get_admin_client


def _parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        created = value
    else:
        created = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return created


def _video_from_row(row: dict) -> VideoInternal:
    return VideoInternal(
        video_id=row["video_id"],
        user_id=str(row["user_id"]),
        camera_id=row["camera_id"],
        filename=row["filename"],
        original_filename=row["original_filename"],
        stored_path=row["storage_path"],
        status=row["status"],
        created_at=_parse_dt(row["created_at"]),
        size_bytes=int(row.get("size_bytes") or 0),
        duration_seconds=row.get("duration_seconds"),
        error=row.get("error"),
        events_materialized=bool(row.get("events_materialized")),
        current_stage=row.get("current_stage"),
        overall_progress=float(row.get("overall_progress") or 0.0),
        stage_states=dict(row.get("stage_states") or {}),
        stage_progress={key: float(value) for key, value in (row.get("stage_progress") or {}).items()},
    )


def _event_from_row(row: dict) -> EventRecord:
    return EventRecord.model_validate(
        {
            "event_id": row["event_id"],
            "video_id": row["video_id"],
            "camera_id": row["camera_id"],
            "start_timestamp": row["start_timestamp"],
            "end_timestamp": row["end_timestamp"],
            "caption": row["caption"],
            "detected_classes": row.get("detected_classes") or [],
            "bounding_boxes": row.get("bounding_boxes") or [],
            "thumbnail_path": row["thumbnail_path"],
            "confidence_score": row["confidence_score"],
            "thumbnail_url": row.get("thumbnail_url"),
            "caption_source": row.get("caption_source"),
            "object_count": row.get("object_count") or 1,
            "embedding_model": row.get("embedding_model"),
            "embedding_model_version": row.get("embedding_model_version"),
        }
    )


def _ready_patch() -> dict:
    return {
        "events_materialized": True,
        "status": "ready",
        "error": None,
        "current_stage": None,
        "overall_progress": 100.0,
        "stage_states": {key: "complete" for key in STAGE_KEYS},
        "stage_progress": {key: 100.0 for key in STAGE_KEYS},
    }


class SupabaseCatalog:
    def clear(self) -> None:
        return

    def load(self) -> None:
        return

    def seed_demo_user(self):
        return None

    def put_video(self, video: VideoInternal) -> VideoInternal:
        client = get_admin_client()
        payload = {
            "video_id": video.video_id,
            "user_id": video.user_id,
            "camera_id": video.camera_id,
            "filename": video.filename,
            "original_filename": video.original_filename,
            "storage_path": video.stored_path,
            "status": video.status,
            "duration_seconds": video.duration_seconds,
            "size_bytes": video.size_bytes,
            "error": video.error,
            "events_materialized": video.events_materialized,
            "current_stage": video.current_stage,
            "overall_progress": video.overall_progress,
            "stage_states": video.stage_states,
            "stage_progress": video.stage_progress,
            "created_at": video.created_at.isoformat(),
        }
        client.table("videos").upsert(payload).execute()
        return video

    def get_video(self, video_id: str) -> VideoInternal | None:
        client = get_admin_client()
        result = client.table("videos").select("*").eq("video_id", video_id).limit(1).execute()
        rows = result.data or []
        if not rows:
            return None
        return _video_from_row(rows[0])

    def list_videos(self, user_id: str) -> list[VideoInternal]:
        client = get_admin_client()
        result = (
            client.table("videos")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [_video_from_row(row) for row in (result.data or [])]

    def set_video_status(
        self,
        video_id: str,
        status: VideoStatus,
        error: str | None = None,
    ) -> None:
        get_admin_client().table("videos").update({"status": status, "error": error}).eq(
            "video_id", video_id
        ).execute()

    def begin_pipeline(self, video_id: str) -> None:
        get_admin_client().table("videos").update(
            {
                "status": "processing",
                "error": None,
                "events_materialized": False,
                "current_stage": "ingest",
                "stage_states": {key: ("complete" if key == "ingest" else "pending") for key in STAGE_KEYS},
                "stage_progress": {key: (100.0 if key == "ingest" else 0.0) for key in STAGE_KEYS},
                "overall_progress": 100.0 / len(STAGE_KEYS),
            }
        ).eq("video_id", video_id).execute()

    def update_stage(self, video_id: str, key: str, progress: float, state: str) -> None:
        video = self.get_video(video_id)
        if video is None or key not in STAGE_KEYS:
            return
        if not video.stage_states:
            video.stage_states = {item: "pending" for item in STAGE_KEYS}
            video.stage_progress = {item: 0.0 for item in STAGE_KEYS}
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
        get_admin_client().table("videos").update(
            {
                "status": video.status,
                "events_materialized": video.events_materialized,
                "current_stage": video.current_stage if video.status != "ready" else None,
                "overall_progress": video.overall_progress,
                "stage_states": video.stage_states,
                "stage_progress": video.stage_progress,
            }
        ).eq("video_id", video_id).execute()

    def fail_pipeline(self, video_id: str, error: str, failed_key: str | None = None) -> None:
        video = self.get_video(video_id)
        key = failed_key or (video.current_stage if video else None) or "ingest"
        states = dict(video.stage_states) if video else {item: "pending" for item in STAGE_KEYS}
        states[key] = "failed"
        get_admin_client().table("videos").update(
            {
                "status": "failed",
                "error": error,
                "current_stage": key,
                "stage_states": states,
            }
        ).eq("video_id", video_id).execute()

    def set_events(
        self,
        video_id: str,
        events: list[EventRecord],
        embeddings: list[list[float]] | None = None,
    ) -> None:
        client = get_admin_client()
        video = self.get_video(video_id)
        if video is None:
            raise RuntimeError(f"Cannot index events; video {video_id} is missing")
        user_id = video.user_id
        embedding_model = current_embedding_model()
        embedding_model_version = current_embedding_model_version()
        client.table("events").delete().eq("video_id", video_id).execute()
        rows = []
        for index, event in enumerate(events):
            row = {
                "event_id": event.event_id,
                "video_id": event.video_id,
                "user_id": user_id,
                "camera_id": event.camera_id,
                "start_timestamp": event.start_timestamp,
                "end_timestamp": event.end_timestamp,
                "caption": event.caption,
                "detected_classes": event.detected_classes,
                "bounding_boxes": [box.model_dump() for box in event.bounding_boxes],
                "thumbnail_path": event.thumbnail_path,
                "thumbnail_url": event.thumbnail_url,
                "confidence_score": event.confidence_score,
                "caption_source": event.caption_source,
                "object_count": event.object_count,
                "embedding_model": embedding_model,
            }
            if embedding_model_version:
                row["embedding_model_version"] = embedding_model_version
            if embeddings and index < len(embeddings) and embeddings[index]:
                row["embedding"] = embeddings[index]
            rows.append(row)
        if rows:
            try:
                client.table("events").insert(rows).execute()
            except Exception:
                for row in rows:
                    row.pop("object_count", None)
                    row.pop("embedding_model", None)
                    row.pop("embedding_model_version", None)
                client.table("events").insert(rows).execute()
        client.table("videos").update(_ready_patch()).eq("video_id", video_id).execute()

    def get_events(self, video_id: str) -> list[EventRecord]:
        columns = (
            "event_id,video_id,camera_id,start_timestamp,end_timestamp,caption,"
            "detected_classes,bounding_boxes,thumbnail_path,thumbnail_url,"
            "confidence_score,caption_source,object_count,embedding_model,embedding_model_version"
        )
        try:
            result = (
                get_admin_client()
                .table("events")
                .select(columns)
                .eq("video_id", video_id)
                .order("start_timestamp")
                .execute()
            )
        except Exception:
            fallback = (
                columns.replace(",object_count", "")
                .replace(",embedding_model_version", "")
                .replace(",embedding_model", "")
            )
            result = (
                get_admin_client()
                .table("events")
                .select(fallback)
                .eq("video_id", video_id)
                .order("start_timestamp")
                .execute()
            )
        return [_event_from_row(row) for row in (result.data or [])]

    def match_events(
        self,
        video_id: str,
        query_embedding: list[float],
        top_k: int,
        user_id: str | None = None,
    ) -> list[tuple[str, float]]:
        client = get_admin_client()
        params: dict = {
            "query_embedding": query_embedding,
            "filter_video_id": video_id,
            "match_count": top_k,
        }
        if user_id:
            params["filter_user_id"] = user_id
        try:
            result = client.rpc("match_events", params).execute()
        except Exception:
            params.pop("filter_user_id", None)
            result = client.rpc("match_events", params).execute()
        rows = result.data or []
        matched: list[tuple[str, float]] = []
        for row in rows:
            event_id = row.get("event_id")
            if not event_id:
                continue
            matched.append((event_id, float(row.get("similarity") or 0.0)))
        return matched

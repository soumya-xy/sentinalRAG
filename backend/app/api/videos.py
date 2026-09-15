import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.auth import UserPublic
from app.models.video import VideoListResponse, VideoRecord, VideoStatusResponse
from app.pipeline.sampling import probe_video
from app.services.object_storage import upload_video
from app.services.processing import build_status, enqueue_ingest
from app.services.store import VideoInternal, now_utc, store

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".m4v": "video/x-m4v",
}


def to_record(video: VideoInternal) -> VideoRecord:
    return VideoRecord(
        video_id=video.video_id,
        camera_id=video.camera_id,
        filename=video.filename,
        original_filename=video.original_filename,
        status=video.status,
        duration_seconds=video.duration_seconds,
        created_at=video.created_at,
        size_bytes=video.size_bytes,
    )


def owned_video(video_id: str, user: UserPublic) -> VideoInternal:
    video = store.get_video(video_id)
    if video is None or video.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


def _probe_duration(payload: bytes, suffix: str) -> float | None:
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(payload)
        tmp.close()
        duration, _ = probe_video(Path(tmp.name))
        return duration
    finally:
        Path(tmp.name).unlink(missing_ok=True)


@router.get("", response_model=VideoListResponse)
def list_videos(user: UserPublic = Depends(get_current_user)) -> VideoListResponse:
    videos = [to_record(item) for item in store.list_videos(user.user_id)]
    return VideoListResponse(videos=videos)


@router.post("", response_model=VideoRecord, status_code=status.HTTP_201_CREATED)
async def upload_video_endpoint(
    file: UploadFile = File(...),
    camera_id: str = Form(default="cam-01"),
    user: UserPublic = Depends(get_current_user),
) -> VideoRecord:
    original = file.filename or "upload.mp4"
    suffix = Path(original).suffix.lower() or ".mp4"
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video type. Use one of: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    settings = get_settings()
    video_id = f"vid_{uuid4().hex[:10]}"
    filename = f"{video_id}{suffix}"
    if settings.supabase_enabled:
        stored_path = upload_video(
            user.user_id,
            video_id,
            suffix,
            payload,
            CONTENT_TYPES.get(suffix, "application/octet-stream"),
        )
        duration = _probe_duration(payload, suffix)
    else:
        stored_path = f"memory/{user.user_id}/{filename}"
        duration = None

    camera = (camera_id or "cam-01").strip() or "cam-01"
    video = VideoInternal(
        video_id=video_id,
        user_id=user.user_id,
        camera_id=camera,
        filename=filename,
        original_filename=original,
        stored_path=stored_path,
        status="uploaded",
        created_at=now_utc(),
        size_bytes=len(payload),
        duration_seconds=duration,
    )
    store.put_video(video)
    enqueue_ingest(video.video_id)
    refreshed = store.get_video(video_id) or video
    return to_record(refreshed)


@router.get("/{video_id}", response_model=VideoRecord)
def get_video(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoRecord:
    video = owned_video(video_id, user)
    return to_record(video)


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoStatusResponse:
    video = owned_video(video_id, user)
    return build_status(video)

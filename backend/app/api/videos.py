from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.auth import UserPublic
from app.models.video import VideoListResponse, VideoRecord, VideoStatusResponse
from app.services.processing import compute_status
from app.services.storage import ensure_storage_dirs, write_bytes
from app.services.store import VideoInternal, now_utc, store

router = APIRouter(prefix="/api/videos", tags=["videos"])

ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


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


@router.get("", response_model=VideoListResponse)
def list_videos(user: UserPublic = Depends(get_current_user)) -> VideoListResponse:
    videos = [to_record(item) for item in store.list_videos(user.user_id)]
    return VideoListResponse(videos=videos)


@router.post("", response_model=VideoRecord, status_code=status.HTTP_201_CREATED)
async def upload_video(
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

    settings = get_settings()
    ensure_storage_dirs(settings)
    video_id = f"vid_{uuid4().hex[:10]}"
    filename = f"{video_id}{suffix}"
    stored_path = settings.videos_dir / filename
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    write_bytes(stored_path, payload)

    camera = (camera_id or "cam-01").strip() or "cam-01"
    video = VideoInternal(
        video_id=video_id,
        user_id=user.user_id,
        camera_id=camera,
        filename=filename,
        original_filename=original,
        stored_path=str(stored_path),
        status="uploaded",
        created_at=now_utc(),
        size_bytes=len(payload),
        duration_seconds=1020.0,
    )
    store.put_video(video)
    return to_record(video)


@router.get("/{video_id}", response_model=VideoRecord)
def get_video(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoRecord:
    video = owned_video(video_id, user)
    compute_status(video)
    refreshed = store.get_video(video_id)
    return to_record(refreshed or video)


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoStatusResponse:
    video = owned_video(video_id, user)
    return compute_status(video)

import logging
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.models.auth import UserPublic
from app.models.video import VideoListResponse, VideoRecord, VideoStatusResponse
from app.core.context import set_video_id
from app.pipeline.sampling import probe_video
from app.services.content_hash import sha256_hex
from app.services.object_storage import upload_video
from app.services.processing import build_status, enqueue_ingest
from app.services.store import VideoInternal, now_utc, store
from app.services.supabase_client import reset_supabase_clients
from app.services.video_sniff import ALLOWED_SUFFIXES, VideoSniffError, validate_video_payload

logger = logging.getLogger("sentinelrag.videos")

router = APIRouter(prefix="/api/videos", tags=["videos"])

CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".m4v": "video/x-m4v",
}


def to_record(video: VideoInternal, *, duplicate: bool = False) -> VideoRecord:
    return VideoRecord(
        video_id=video.video_id,
        camera_id=video.camera_id,
        filename=video.filename,
        original_filename=video.original_filename,
        status=video.status,
        duration_seconds=video.duration_seconds,
        created_at=video.created_at,
        size_bytes=video.size_bytes,
        content_hash=video.content_hash,
        duplicate=duplicate,
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


@router.post("", response_model=VideoRecord)
async def upload_video_endpoint(
    response: Response,
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

    try:
        validate_video_payload(payload, suffix)
    except VideoSniffError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None

    camera = (camera_id or "cam-01").strip() or "cam-01"
    digest = sha256_hex(payload)
    matches = store.find_videos_by_content_hash(user.user_id, digest)
    ready = next((item for item in matches if item.status == "ready"), None)
    if ready:
        set_video_id(ready.video_id)
        logger.info("Duplicate completed upload reused existing video hash=%s", digest[:12])
        response.status_code = status.HTTP_200_OK
        return to_record(ready, duplicate=True)

    existing = next((item for item in matches if item.status != "ready"), None)
    if existing and existing.status == "processing":
        set_video_id(existing.video_id)
        logger.info("Upload matched an in-progress ingest")
        response.status_code = status.HTTP_200_OK
        return to_record(existing, duplicate=False)
    if existing:
        set_video_id(existing.video_id)
        existing.camera_id = camera
        existing.original_filename = original
        existing.content_hash = digest
        store.put_video(existing)
        logger.info(
            "Reprocessing incomplete/failed upload hash=%s status_was=%s",
            digest[:12],
            existing.status,
        )
        enqueue_ingest(existing.video_id)
        refreshed = store.get_video(existing.video_id) or existing
        response.status_code = status.HTTP_201_CREATED
        return to_record(refreshed, duplicate=False)

    settings = get_settings()
    video_id = f"vid_{uuid4().hex[:10]}"
    set_video_id(video_id)
    filename = f"{video_id}{suffix}"
    if settings.supabase_enabled:
        try:
            stored_path = upload_video(
                user.user_id,
                video_id,
                suffix,
                payload,
                CONTENT_TYPES.get(suffix, "application/octet-stream"),
            )
        except Exception as exc:
            reset_supabase_clients()
            err_str = str(exc)
            if "413" in err_str or "exceeded" in err_str.lower() or "too large" in err_str.lower():
                size_mb = len(payload) / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Video file ({size_mb:.1f} MB) exceeds Supabase Storage file size limit. "
                    "Please upload a smaller video clip or increase the 'Global Max Upload File Size' in Supabase Dashboard -> Storage -> Settings.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload video to Supabase Storage: {err_str}",
            ) from exc
        duration = _probe_duration(payload, suffix)
    else:
        stored_path = f"memory/{user.user_id}/{filename}"
        duration = None

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
        content_hash=digest,
        duration_seconds=duration,
    )
    store.put_video(video)
    logger.info("Upload accepted size_bytes=%s suffix=%s", len(payload), suffix)
    enqueue_ingest(video.video_id)
    refreshed = store.get_video(video_id) or video
    response.status_code = status.HTTP_201_CREATED
    return to_record(refreshed)


@router.get("/{video_id}", response_model=VideoRecord)
def get_video(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoRecord:
    video = owned_video(video_id, user)
    return to_record(video)


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoStatusResponse:
    video = owned_video(video_id, user)
    return build_status(video)


@router.post("/{video_id}/retry", response_model=VideoRecord)
def retry_ingest(video_id: str, user: UserPublic = Depends(get_current_user)) -> VideoRecord:
    video = owned_video(video_id, user)
    if video.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retry is only available after a failed ingest.",
        )
    set_video_id(video.video_id)
    logger.info("Retry ingest requested")
    enqueue_ingest(video.video_id)
    refreshed = store.get_video(video_id) or video
    return to_record(refreshed)

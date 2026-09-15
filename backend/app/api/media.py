from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.core.config import get_settings
from app.services.object_storage import download_thumbnail, thumbnail_object_key
from app.services.store import store

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{video_id}/{filename}")
def get_thumbnail(video_id: str, filename: str) -> Response:
    if "/" in filename or "\\" in filename or ".." in filename or ".." in video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")

    settings = get_settings()
    video = store.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    media_type = "image/svg+xml" if filename.lower().endswith(".svg") else "image/jpeg"
    if not settings.supabase_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    key = thumbnail_object_key(video.user_id, video_id, filename)
    try:
        payload = download_thumbnail(key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found") from exc
    return Response(content=payload, media_type=media_type)

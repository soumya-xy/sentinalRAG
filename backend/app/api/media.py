from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import get_settings

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/{video_id}/{filename}")
def get_thumbnail(video_id: str, filename: str) -> FileResponse:
    if "/" in filename or "\\" in filename or ".." in filename or ".." in video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    settings = get_settings()
    path = settings.thumbnails_dir / video_id / filename
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")
    media_type = "image/svg+xml" if path.suffix == ".svg" else "image/jpeg"
    return FileResponse(path, media_type=media_type)

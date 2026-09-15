from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.auth import UserPublic
from app.models.event import EventListResponse
from app.services.processing import compute_status
from app.services.store import store

router = APIRouter(tags=["events"])


@router.get("/api/videos/{video_id}/events", response_model=EventListResponse)
def list_events(video_id: str, user: UserPublic = Depends(get_current_user)) -> EventListResponse:
    video = store.get_video(video_id)
    if video is None or video.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    snapshot = compute_status(video)
    if snapshot.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Video is still processing. Events are available after indexing completes.",
        )

    events = store.get_events(video_id)
    return EventListResponse(
        video_id=video.video_id,
        camera_id=video.camera_id,
        count=len(events),
        events=events,
    )

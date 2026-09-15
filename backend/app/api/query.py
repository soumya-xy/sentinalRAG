from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.graphs.query_graph import invoke_query_graph
from app.models.auth import UserPublic
from app.models.query import QueryRequest, QueryResponse
from app.services.processing import compute_status
from app.services.store import store

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_video(body: QueryRequest, user: UserPublic = Depends(get_current_user)) -> QueryResponse:
    video = store.get_video(body.video_id)
    if video is None or video.user_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    snapshot = compute_status(video)
    if snapshot.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Index is not ready. Wait for batch processing to finish.",
        )

    events = store.get_events(video.video_id)
    return invoke_query_graph(
        question=body.question.strip(),
        video_id=video.video_id,
        camera_id=video.camera_id,
        events=events,
    )

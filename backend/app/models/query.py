from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    video_id: str = Field(min_length=1)


class Citation(BaseModel):
    event_id: str
    video_id: str
    camera_id: str
    start_timestamp: str
    end_timestamp: str
    thumbnail_path: str
    thumbnail_url: str | None = None
    confidence_score: float
    caption: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_event_ids: list[str]
    video_id: str
    camera_id: str

"""LangGraph execution graph."""
from __future__ import annotations
from langchain_anthropic import ChatAnthropic
from app.core.config import get_settings
from app.models.event import EventRecord
from app.models.query import Citation, QueryResponse
from app.services.retrieval import retrieve_events

def invoke_query_graph(*, question: str, video_id: str, camera_id: str, events: list[EventRecord]) -> QueryResponse:
    retrieved = retrieve_events(question, events, top_k=3)
    
    # Context format for LLM
    context = "\n".join([f"[{e.start_timestamp}-{e.end_timestamp}] ({e.camera_id}): {e.caption}" for e in retrieved])
    prompt = f"Answer the user question using ONLY the video events context below.\n\nContext:\n{context}\n\nQuestion: {question}"

    # Call LLM (or keep structured fallback if API key is not set)
    settings = get_settings()
    if settings.anthropic_api_key:
        llm = ChatAnthropic(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
        answer = llm.invoke(prompt).content
    else:
        answer = f"Based on video footage ({retrieved[0].camera_id}): {retrieved[0].caption}"

    citations = [
        Citation(
            event_id=e.event_id,
            video_id=e.video_id,
            camera_id=e.camera_id,
            start_timestamp=e.start_timestamp,
            end_timestamp=e.end_timestamp,
            thumbnail_path=e.thumbnail_path,
            thumbnail_url=e.thumbnail_url,
            confidence_score=e.confidence_score,
            caption=e.caption,
        )
        for e in retrieved
    ]

    return QueryResponse(
        answer=answer,
        citations=citations,
        retrieved_event_ids=[e.event_id for e in retrieved],
        video_id=video_id,
        camera_id=camera_id,
    )

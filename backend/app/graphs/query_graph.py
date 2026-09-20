"""LangGraph query graph: retrieve → compose → cite."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, TypedDict
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.core.context import bind_log_context, get_query_id, get_request_id, set_query_id, set_video_id
from app.models.event import EventRecord
from app.models.query import Citation, QueryResponse
from app.services.gemini_retry import call_with_backoff
from app.services.llm import get_chat_model, message_text
from app.services.retrieval import retrieve_events

logger = logging.getLogger("sentinelrag.query")


def _get_event_image_b64(event: EventRecord) -> str | None:
    from app.services.object_storage import decode_inline_image, looks_like_inline_image

    for value in (event.thumbnail_path, event.thumbnail_url or ""):
        if looks_like_inline_image(value):
            try:
                raw, _, _ = decode_inline_image(value)
                return base64.b64encode(raw).decode("ascii")
            except Exception as exc:
                logger.debug("Could not decode leftover inline thumbnail for %s: %s", event.event_id, exc)
    if not event.thumbnail_path:
        return None
    try:
        settings = get_settings()
        if settings.supabase_enabled:
            from app.services.object_storage import download_object

            data = download_object(settings.supabase_thumbnails_bucket, event.thumbnail_path)
            return base64.b64encode(data).decode("ascii")
        p = Path(event.thumbnail_path)
        if p.exists() and p.is_file():
            return base64.b64encode(p.read_bytes()).decode("ascii")
    except Exception as exc:
        logger.debug("Could not load event image b64 for %s: %s", event.event_id, exc)
    return None


class QueryState(TypedDict, total=False):
    question: str
    video_id: str
    camera_id: str
    user_id: str
    events: list[EventRecord]
    query_id: str
    retrieved: list[EventRecord]
    answer: str
    answer_source: str
    visual_reinspection_skipped: bool
    citations: list[Citation]


def _fallback_answer(question: str, retrieved: list[EventRecord], camera_id: str) -> str:
    if not retrieved:
        return (
            "No indexed events matched this question. Confirm the video finished processing, "
            "then try a more specific object, clothing, or time reference."
        )
    primary = retrieved[0]
    extras = ""
    if len(retrieved) > 1:
        extras = f" {len(retrieved) - 1} additional supporting event(s) are cited below."
    _ = question
    return (
        f"{primary.caption} Cited window {primary.start_timestamp}–{primary.end_timestamp} "
        f"on {camera_id}.{extras}"
    )


def _retrieve(state: QueryState) -> dict[str, list[EventRecord]]:
    retrieved = retrieve_events(
        state["question"],
        state.get("events") or [],
        video_id=state["video_id"],
        user_id=state.get("user_id"),
    )
    return {"retrieved": retrieved}


def _compose(state: QueryState) -> dict[str, Any]:
    retrieved = state.get("retrieved") or []
    camera_id = state["camera_id"]
    question = state["question"]
    video_id = state["video_id"]
    query_id = state.get("query_id") or get_query_id() or ""
    set_video_id(video_id)
    if query_id:
        set_query_id(query_id)
    if not retrieved:
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "none",
            "visual_reinspection_skipped": False,
        }

    llm = get_chat_model()
    if llm is None:
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "extractive",
            "visual_reinspection_skipped": False,
        }

    context = "\n".join(
        (
            f"- event {event.event_id} | {event.start_timestamp}–{event.end_timestamp} | "
            f"{event.camera_id} | classes={', '.join(event.detected_classes)} | "
            f"scene_count={event.object_count} | confidence={event.confidence_score:.2f} | "
            f"{event.caption}"
        )
        for event in retrieved
    )
    prompt = (
        "Answer the operator question using ONLY the retrieved CCTV events and attached visual frames. "
        "Name the timestamp window and camera_id in the answer. "
        "If the events and visual frames are not enough, say you cannot confirm from the index. "
        "Do not invent people, objects, or times.\n\n"
        f"Events:\n{context}\n\nQuestion: {question}"
    )

    try:
        pass1 = call_with_backoff(
            lambda: llm.invoke(prompt),
            stage="compose_text",
            video_id=video_id,
            query_id=query_id,
        )
        pass1_text = message_text(pass1.content).strip()
        if not pass1_text:
            raise ValueError("empty model answer")
    except Exception as exc:
        logger.warning(
            "Pass-1 text compose failed; using extractive fallback. video_id=%s query_id=%s err=%s",
            video_id,
            query_id,
            exc,
        )
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "extractive",
            "visual_reinspection_skipped": False,
        }

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for event in retrieved:
        img_b64 = _get_event_image_b64(event)
        if img_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                }
            )

    if len(content) <= 1:
        return {
            "answer": pass1_text,
            "answer_source": "llm",
            "visual_reinspection_skipped": False,
        }

    try:
        pass2 = call_with_backoff(
            lambda: llm.invoke([HumanMessage(content=content)]),
            stage="visual_reinspection",
            video_id=video_id,
            query_id=query_id,
        )
        text = message_text(pass2.content).strip()
        if not text:
            raise ValueError("empty model answer")
        return {
            "answer": text,
            "answer_source": "llm",
            "visual_reinspection_skipped": False,
        }
    except Exception as exc:
        logger.warning(
            "Visual re-inspection skipped after retries; returning Pass-1 text answer. "
            "video_id=%s query_id=%s err=%s",
            video_id,
            query_id,
            exc,
        )
        return {
            "answer": pass1_text,
            "answer_source": "llm",
            "visual_reinspection_skipped": True,
        }


def _cite(state: QueryState) -> dict[str, list[Citation]]:
    from app.services.object_storage import attach_signed_thumbnail_urls

    retrieved = attach_signed_thumbnail_urls(list(state.get("retrieved") or []))
    citations = [
        Citation(
            event_id=event.event_id,
            video_id=event.video_id,
            camera_id=event.camera_id,
            start_timestamp=event.start_timestamp,
            end_timestamp=event.end_timestamp,
            thumbnail_path=event.thumbnail_path,
            thumbnail_url=event.thumbnail_url,
            confidence_score=event.confidence_score,
            caption=event.caption,
            caption_source=event.caption_source,
        )
        for event in retrieved
    ]
    return {"citations": citations}


def build_query_graph():
    graph = StateGraph(QueryState)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("compose", _compose)
    graph.add_node("cite", _cite)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", "cite")
    graph.add_edge("cite", END)
    return graph.compile()


_GRAPH = None


def _graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_query_graph()
    return _GRAPH


def invoke_query_graph(
    *,
    question: str,
    video_id: str,
    camera_id: str,
    events: list[EventRecord],
    user_id: str | None = None,
) -> QueryResponse:
    query_id = get_query_id() or get_request_id() or f"qry_{uuid4().hex[:10]}"
    set_query_id(query_id)
    set_video_id(video_id)
    with bind_log_context(video_id=video_id, query_id=query_id):
        result = _graph().invoke(
            {
                "question": question,
                "video_id": video_id,
                "camera_id": camera_id,
                "user_id": user_id or "",
                "query_id": query_id,
                "events": events,
            }
        )
    retrieved = result.get("retrieved") or []
    answer_source = result.get("answer_source") or ("none" if not retrieved else "extractive")
    skipped = bool(result.get("visual_reinspection_skipped"))
    return QueryResponse(
        answer=result.get("answer") or _fallback_answer(question, retrieved, camera_id),
        citations=result.get("citations") or [],
        retrieved_event_ids=[event.event_id for event in retrieved],
        video_id=video_id,
        camera_id=camera_id,
        provenance=_provenance(retrieved, answer_source, skipped),
        answer_source=answer_source,
        visual_reinspection_skipped=skipped,
        query_id=query_id,
    )


def _provenance(
    retrieved: list[EventRecord],
    answer_source: str,
    visual_reinspection_skipped: bool = False,
) -> str:
    if not retrieved:
        return (
            "Nothing in this video's event index was similar enough. "
            "The line below is a status message, not a description of the footage."
        )
    windows = ", ".join(
        f"{event.start_timestamp}–{event.end_timestamp}" for event in retrieved[:3]
    )
    if answer_source == "llm" and visual_reinspection_skipped:
        return (
            f"Searched this video's index and retrieved {len(retrieved)} event(s) "
            f"({windows}). Gemini wrote a text-only answer from those captions. "
            "Visual re-inspection of cited frames was skipped after Gemini retries."
        )
    if answer_source == "llm":
        return (
            f"Searched this video's index and retrieved {len(retrieved)} event(s) "
            f"({windows}). Gemini wrote the answer using only those stored captions "
            "and the cited frames."
        )
    return (
        f"Searched this video's index and retrieved {len(retrieved)} event(s) "
        f"({windows}). The model was unavailable, so the answer is the top event's "
        "stored caption — not a newly invented scene."
    )

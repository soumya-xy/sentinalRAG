"""LangGraph query graph: retrieve → compose → cite."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.models.event import EventRecord
from app.models.query import Citation, QueryResponse
from app.services.llm import get_chat_model, message_text
from app.services.retrieval import retrieve_events

logger = logging.getLogger("sentinelrag.query")


def _get_event_image_b64(event: EventRecord) -> str | None:
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
    retrieved: list[EventRecord]
    answer: str
    answer_source: str
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


def _compose(state: QueryState) -> dict[str, str]:
    retrieved = state.get("retrieved") or []
    camera_id = state["camera_id"]
    question = state["question"]
    if not retrieved:
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "none",
        }

    llm = get_chat_model()
    if llm is None:
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "extractive",
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

    # Build multimodal content for Visual Re-Inspection
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

    try:
        if len(content) > 1:
            try:
                result = llm.invoke([HumanMessage(content=content)])
            except Exception as mm_exc:
                logger.info("Multimodal prompt failed, falling back to text-only prompt: %s", mm_exc)
                result = llm.invoke(prompt)
        else:
            result = llm.invoke(prompt)

        text = message_text(result.content).strip()
        if not text:
            raise ValueError("empty model answer")
        return {"answer": text, "answer_source": "llm"}
    except Exception as exc:
        logger.warning("LLM compose failed, using extractive fallback: %s", exc)
        return {
            "answer": _fallback_answer(question, retrieved, camera_id),
            "answer_source": "extractive",
        }


def _cite(state: QueryState) -> dict[str, list[Citation]]:
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
        for event in (state.get("retrieved") or [])
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
    result = _graph().invoke(
        {
            "question": question,
            "video_id": video_id,
            "camera_id": camera_id,
            "user_id": user_id or "",
            "events": events,
        }
    )
    retrieved = result.get("retrieved") or []
    answer_source = result.get("answer_source") or ("none" if not retrieved else "extractive")
    return QueryResponse(
        answer=result.get("answer") or _fallback_answer(question, retrieved, camera_id),
        citations=result.get("citations") or [],
        retrieved_event_ids=[event.event_id for event in retrieved],
        video_id=video_id,
        camera_id=camera_id,
        provenance=_provenance(retrieved, answer_source),
        answer_source=answer_source,
    )


def _provenance(retrieved: list[EventRecord], answer_source: str) -> str:
    if not retrieved:
        return (
            "Nothing in this video's event index was similar enough. "
            "The line below is a status message, not a description of the footage."
        )
    windows = ", ".join(
        f"{event.start_timestamp}–{event.end_timestamp}" for event in retrieved[:3]
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

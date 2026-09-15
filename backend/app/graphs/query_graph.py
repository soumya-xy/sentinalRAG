"""LangGraph query graph: retrieve → compose → cite."""

from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.models.event import EventRecord
from app.models.query import Citation, QueryResponse
from app.services.llm import get_chat_model, message_text
from app.services.retrieval import retrieve_events

logger = logging.getLogger("sentinelrag.query")


class QueryState(TypedDict, total=False):
    question: str
    video_id: str
    camera_id: str
    events: list[EventRecord]
    retrieved: list[EventRecord]
    answer: str
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
        top_k=3,
    )
    return {"retrieved": retrieved}


def _compose(state: QueryState) -> dict[str, str]:
    retrieved = state.get("retrieved") or []
    camera_id = state["camera_id"]
    question = state["question"]
    if not retrieved:
        return {"answer": _fallback_answer(question, retrieved, camera_id)}

    llm = get_chat_model()
    if llm is None:
        return {"answer": _fallback_answer(question, retrieved, camera_id)}

    context = "\n".join(
        (
            f"- event {event.event_id} | {event.start_timestamp}–{event.end_timestamp} | "
            f"{event.camera_id} | classes={', '.join(event.detected_classes)} | "
            f"confidence={event.confidence_score:.2f} | {event.caption}"
        )
        for event in retrieved
    )
    prompt = (
        "Answer the operator question using ONLY the retrieved CCTV events. "
        "Name the timestamp window and camera_id in the answer. "
        "If the events are not enough, say you cannot confirm from the index. "
        "Do not invent people, objects, or times.\n\n"
        f"Events:\n{context}\n\nQuestion: {question}"
    )
    try:
        result = llm.invoke(prompt)
        text = message_text(result.content).strip()
        if not text:
            raise ValueError("empty model answer")
        return {"answer": text}
    except Exception as exc:
        logger.warning("LLM compose failed, using extractive fallback: %s", exc)
        return {"answer": _fallback_answer(question, retrieved, camera_id)}


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
) -> QueryResponse:
    result = _graph().invoke(
        {
            "question": question,
            "video_id": video_id,
            "camera_id": camera_id,
            "events": events,
        }
    )
    retrieved = result.get("retrieved") or []
    return QueryResponse(
        answer=result.get("answer") or _fallback_answer(question, retrieved, camera_id),
        citations=result.get("citations") or [],
        retrieved_event_ids=[event.event_id for event in retrieved],
        video_id=video_id,
        camera_id=camera_id,
    )

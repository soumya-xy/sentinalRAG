# Project Overview: SentinelRAG — Video Surveillance RAG System

This file is the single source of truth for this project. Any AI coding assistant working on this repo should read this file fully before writing code, and should treat it as authoritative over assumptions made from general training knowledge.

---

## 1. What This Project Is

SentinelRAG lets a user upload a pre-recorded CCTV/surveillance video and ask natural-language questions about its contents ("Did anyone in a red jacket enter after 9pm?", "How many people appeared in the last 10 minutes?"). The system detects objects/events in the video, generates natural-language descriptions of those events, indexes them for retrieval, and answers user questions using a RAG (Retrieval-Augmented Generation) pipeline — grounding every answer in a specific timestamp, camera/video ID, and thumbnail frame.

This is **not** a live/real-time surveillance system. Video is uploaded, processed once in batch, and then queried repeatedly. This mirrors how real enterprise video-search products (e.g., Verkada, Axis) are architected: index first, query later.

**One-line pitch (for README/resume use):**
> A video-surveillance RAG system combining YOLO11 detection, Gemini event captioning, and Supabase pgvector retrieval, enabling natural-language querying of recorded CCTV footage with timestamp-grounded answers and visual citations.

---

## 2. Author Context

Built by a B.Tech CS student with prior experience in:
- CNN-based computer vision (mobile phone grading pipeline internship)
- Multi-agent RAG systems (prior project: RAGHive — LangGraph, ChromaDB, BGE-M3, XAI attribution)
- Deep learning fundamentals, CNNs, YOLO (via coursework/certifications)

This project is deliberately positioned as the connective piece between the author's CV background and RAG background — every architectural choice below should reinforce that narrative, not dilute it with unrelated tech.

---

## 3. Build Phases (IMPORTANT — do not skip ahead)

**Phase 1 — Single video, full pipeline (current phase unless stated otherwise):**
Get one video working end-to-end through every stage below. Goal is a working vertical slice, not breadth. Even in Phase 1, the data schema (Section 6) must already include `video_id`/`camera_id` fields — this is a forward-compatibility requirement, not scope creep.

**Phase 2 — Multiple videos/cameras:**
Only begin after Phase 1 is fully working and demo-able. Extends the same pipeline across multiple files, enables cross-camera queries ("which camera saw the red car"). Should require no schema redesign if Phase 1 was built correctly.

**Do not silently expand scope to multi-video, live streaming, or real-time processing unless explicitly instructed. These are explicitly out of scope for the current build.**

---

## 4. Explicit Design Decisions (do not re-litigate these without discussion)

| Decision | Choice | Why |
|---|---|---|
| Processing mode | Batch (offline), not live/real-time | Avoids streaming infra complexity; matches real-world enterprise video search products; keeps scope achievable solo |
| Detection model | Ultralytics **YOLO11** (not YOLOv8, not YOLO26) | Stronger small/cluttered-object performance than YOLOv8; more mature/documented than the newer YOLO26; widely recognized by recruiters |
| Detection weights | Pretrained COCO weights by default; light fine-tuning on a small custom subset is a stretch goal, not a requirement | Avoids the cost/time of training from scratch; COCO already covers person/vehicle/bag classes needed here |
| Captioning model | **Gemini 2.0 Flash (API)** when no local GPU/vLLM is available; **Qwen2.5-VL (3B/7B)** remains the local option | Phase 1 is runnable with a Gemini API key only. Local Qwen2.5-VL is the original design and stays documented for a later GPU box; it is not required to leave demo mode. |
| Captioning trigger | Two-stage: cheap YOLO detection flags "interesting" frames/windows first; expensive VLM captioning only runs on flagged frames | Avoids running a heavy VLM on every sampled frame; real system-design pattern worth calling out explicitly in docs/interviews |
| Fallback captioning | Rule-based template captions (e.g., "person detected, red shirt, 14:32") if the Gemini key is missing or a vision call fails | Keeps ingest from dying when the API is rate-limited or offline |
| Answer-generation LLM | **Gemini** via LangGraph (`LLM_PROVIDER=google`) | Matches the author's available API; Anthropic/OpenAI stay in config but are not required |
| Embeddings | **Gemini text-embedding-004** (768-d) by default; **BGE-M3** if `EMBEDDING_PROVIDER=local` | Same vectors are stored in Supabase pgvector. Local BGE-M3 is optional. |
| Vector database | **Supabase pgvector** (replaces ChromaDB) | One hosted Postgres for events + similarity search. Requested explicitly so nothing is persisted on the laptop. |
| Object storage | **Supabase Storage** (videos + thumbnails) | Per-user object keys. The API only uses OS temp files while YOLO runs, then deletes them. |
| Auth | **Supabase Auth** | Replaces the in-memory JWT demo users. Each account only sees its own videos. |
| Orchestration | **LangGraph** | Consistent with author's existing framework experience; shows depth in one framework rather than scattered tools |
| Backend | **FastAPI** | Consistent with author's stack; lightweight, async-friendly |
| Frame sampling | Fixed interval (e.g., 1 frame every 1–2 sec) or scene-change detection via OpenCV — not every frame | Reduces redundant processing; every-frame processing is unnecessary and expensive |
| Scope boundary | Single video first, multiple videos second (see Section 3) | Prevents premature complexity; schema is designed up front to make Phase 2 additive, not a rewrite |

If a future prompt asks to change one of these (e.g., "let's make it live" or "switch to Pinecone"), flag that it contradicts a documented decision and confirm before proceeding.

---

## 5. Pipeline Architecture

```
[Video Upload]
      │
      ▼
[Frame Sampling]  (OpenCV — fixed interval or scene-change detection)
      │
      ▼
[Detection]  (YOLO11 — pretrained COCO weights)
      │  → bounding boxes, class labels, rough attributes (position, count)
      ▼
[Event Construction]  (group consecutive detections into time-bounded "events")
      │  e.g., "person present from 00:14:20–00:14:45"
      ▼
[Captioning]  (Gemini vision on flagged frames; rule-based fallback; Qwen2.5-VL if a local GPU is added later)
      │  → natural language description of each event
      ▼
[Indexing]  (embed captions + metadata into Supabase Postgres / pgvector)
      │  metadata: video_id/camera_id, timestamp range, thumbnail path, bounding box, confidence
      ▼
[Query Time]
      User asks a natural-language question
      │
      ▼
[Retrieval]  (Supabase pgvector similarity search over event captions)
      │
      ▼
[Answer Generation]  (LLM via LangGraph — answers with citation: timestamp + camera + thumbnail)
```

Only the upload → indexing path is "slow" (one-time batch processing, shown as a progress indicator in the UI). Query time is fast and should feel real-time to the user even though the video was processed beforehand.

---

## 6. Data Schema (must be respected from Phase 1 onward)

Every indexed "event" record must include, at minimum:

- `event_id` — unique identifier
- `video_id` / `camera_id` — REQUIRED even in single-video Phase 1, for forward compatibility with Phase 2
- `start_timestamp`, `end_timestamp` — time range of the event within the video
- `caption` — natural language description (VLM-generated or rule-based)
- `detected_classes` — list of object classes involved (e.g., ["person", "car"])
- `bounding_boxes` — coordinates per relevant frame or a representative frame
- `thumbnail_path` — path to a representative frame image for UI display
- `confidence_score` — detection/caption confidence, used for retrieval ranking and XAI-style transparency

Do not build the schema without `video_id`/`camera_id` even if only one video exists — retrofitting this later causes avoidable rework.

---

## 7. Explicit Non-Goals (out of scope unless the author says otherwise)

- Live/real-time camera streaming or RTSP ingestion
- Training a detection model from scratch
- Multi-camera support before Phase 1 is complete and demo-able
- Switching vector databases (e.g., to Pinecone/Weaviate) — noted as a "production scaling" talking point only, not something to implement now
- Frontier/very new VLMs (e.g., Qwen3-VL, Molmo2) — noted as future-work talking points, not required for the current build

---

## 8. Documentation Files Expected in This Repo

- `README.md` — project overview, demo, setup instructions
- `ARCHITECTURE.md` — expanded version of Section 5, with diagrams
- `DESIGN_DECISIONS.md` — expanded version of Section 4, with rationale and alternatives considered
- `EVALUATION.md` — detection accuracy, retrieval precision/recall, sample queries and results, known failure cases
- `SCHEMA.md` — expanded version of Section 6
- `LIMITATIONS.md` — expanded version of Section 7
- `ROADMAP.md` — Phase 2 (multi-video) and beyond

This `CLAUDE.md` file should stay in sync with the above if any core decision changes — update this file first, then propagate the change to the relevant detailed doc.

---

## 9. How an AI Assistant Should Use This File

- Treat Section 4 (Design Decisions) as binding unless the author explicitly revisits it.
- Treat Section 3 (Build Phases) as a gate — do not implement Phase 2 features while Phase 1 is incomplete.
- Treat Section 6 (Schema) as the contract for any code touching detection output, captioning output, or pgvector records.
- If a request conflicts with this file, point out the conflict before proceeding rather than silently overriding it.

# Data Flow Diagrams — SentinelRAG (Video Surveillance RAG)

This file contains the Level 0 (Context), Level 1 (System Overview), and Level 2 (Detailed Sub-process) Data Flow Diagrams for the project. Diagrams are written in Mermaid so they render directly in GitHub, most IDEs, and Claude/VS Code markdown previews.

Notation used:
- **Rounded rectangle** = Process
- **Rectangle** = External Entity
- **Cylinder** = Data Store
- **Arrow label** = Data Flow

---

## Level 0 — Context Diagram

The system as a single black box, showing only external entities and the data crossing the system boundary.

```mermaid
flowchart LR
    User([User])
    Sys((SentinelRAG System))
    SB[(Supabase
    Auth / Storage / pgvector)]
    Gemini([Gemini API])

    User -- "Video file (upload)" --> Sys
    User -- "Natural language question" --> Sys
    Sys -- "Answer + timestamp + thumbnail citation" --> User
    Sys -- "Processing status / progress" --> User
    Sys -- "Auth, objects, event rows, vectors" --> SB
    SB -- "Sessions, files, retrieved events" --> Sys
    Sys -- "Captions / embeddings / answers" --> Gemini
    Gemini -- "Text + vectors" --> Sys
```

**Description:** A user uploads a video and later asks natural-language questions. SentinelRAG persists nothing on the laptop: Supabase holds accounts, files, and pgvector rows. Gemini provides vision captions, embeddings, and answers. No live camera feeds.

---

## Level 1 — System-Level DFD

Decomposes the system into its major processes and data stores.

```mermaid
flowchart TD
    User([User])

    P1(("1.0
    Upload &
    Ingest Video"))
    P2(("2.0
    Detect & Caption
    Events"))
    P3(("3.0
    Index
    Events"))
    P4(("4.0
    Process
    User Query"))
    P5(("5.0
    Generate
    Grounded Answer"))

    DS1[(Supabase Storage
    videos)]
    DS2[(Supabase Postgres
    pgvector)]
    DS3[(Supabase Storage
    thumbnails)]

    User -- "Video file" --> P1
    P1 -- "Stored video" --> DS1
    P1 -- "Video reference / video_id" --> P2

    DS1 -- "Video frames" --> P2
    P2 -- "Event records
    (caption, bbox, timestamp, class)" --> P3
    P2 -- "Frame thumbnails" --> DS3

    P3 -- "Embedded event records" --> DS2

    User -- "Natural language question" --> P4
    P4 -- "Query embedding" --> DS2
    DS2 -- "Top-k matching events" --> P4

    P4 -- "Retrieved events + query" --> P5
    DS3 -- "Thumbnail for cited event" --> P5
    P5 -- "Answer + timestamp + camera + thumbnail" --> User
```

**Description of processes:**
- **1.0 Upload & Ingest Video** — accepts the uploaded file, assigns a `video_id`, stores it.
- **2.0 Detect & Caption Events** — samples frames, runs YOLO11 detection, constructs time-bounded events, generates natural-language captions (Gemini vision, or rule-based fallback).
- **3.0 Index Events** — embeds event captions/metadata and writes them into Supabase Postgres (pgvector).
- **4.0 Process User Query** — embeds the user's question, retrieves the most relevant events from pgvector.
- **5.0 Generate Grounded Answer** — uses an LLM (via LangGraph) to compose a natural-language answer citing timestamp, camera/video ID, and thumbnail.

---

## Level 2 — Detailed Decomposition

### Level 2a — Decomposition of Process 2.0 (Detect & Caption Events)

```mermaid
flowchart TD
    DS1[(Video Storage)]

    P2_1(("2.1
    Frame
    Sampling"))
    P2_2(("2.2
    Object
    Detection
    (YOLO11)"))
    P2_3(("2.3
    Event
    Construction"))
    P2_4(("2.4
    Event
    Captioning
    (Gemini /
    rule-based)"))

    DS3[(Thumbnail Storage)]
    DS4[(Raw Detections
    Buffer)]

    DS1 -- "Video file" --> P2_1
    P2_1 -- "Sampled frames
    (fixed interval /
    scene-change)" --> P2_2

    P2_2 -- "Bounding boxes,
    class labels,
    confidence scores" --> DS4
    P2_2 -- "Flagged 'interesting'
    frames" --> P2_4

    DS4 -- "Per-frame detections" --> P2_3
    P2_3 -- "Time-bounded events
    (start/end timestamp,
    involved classes)" --> P2_4
    P2_3 -- "Representative frame" --> DS3

    P2_4 -- "Event caption text" --> P3_OUT(("To 3.0
    Index Events"))
```

**Description:**
- **2.1 Frame Sampling** — extracts frames at a fixed interval or via scene-change detection (avoids processing every frame).
- **2.2 Object Detection** — runs YOLO11 on sampled frames; flags frames with meaningful detections for captioning (the two-stage cheap-detector → expensive-captioner design).
- **2.3 Event Construction** — groups consecutive per-frame detections into human-meaningful, time-bounded events.
- **2.4 Event Captioning** — generates a natural-language description per event, using Gemini vision on flagged frames, or a rule-based template as fallback.

---

### Level 2b — Decomposition of Processes 4.0 + 5.0 (Query → Answer)

```mermaid
flowchart TD
    User([User])
    DS2[(Event Store
    pgvector)]
    DS3[(Thumbnail Storage)]

    P4_1(("4.1
    Parse &
    Embed Query"))
    P4_2(("4.2
    Similarity
    Retrieval"))
    P4_3(("4.3
    Rank / Filter
    Results"))
    P5_1(("5.1
    LLM Answer
    Composition"))
    P5_2(("5.2
    Citation
    Assembly"))

    User -- "Natural language question" --> P4_1
    P4_1 -- "Query embedding" --> P4_2
    DS2 -- "Candidate events
    (captions + metadata)" --> P4_2

    P4_2 -- "Top-k similar events" --> P4_3
    P4_3 -- "Filtered/ranked events
    (by confidence, recency,
    video/camera_id)" --> P5_1

    P5_1 -- "Draft answer text" --> P5_2
    P4_3 -- "Selected event metadata
    (timestamp, video_id)" --> P5_2
    DS3 -- "Thumbnail image" --> P5_2

    P5_2 -- "Final answer +
    timestamp + camera +
    thumbnail citation" --> User
```

**Description:**
- **4.1 Parse & Embed Query** — converts the user's natural-language question into a vector embedding.
- **4.2 Similarity Retrieval** — queries pgvector for the most semantically similar indexed events.
- **4.3 Rank / Filter Results** — applies confidence thresholds and any filters (e.g., specific camera/video, time range) before passing results forward.
- **5.1 LLM Answer Composition** — an LLM (orchestrated via LangGraph) drafts a natural-language answer grounded in the retrieved events.
- **5.2 Citation Assembly** — attaches the supporting timestamp, camera/video ID, and thumbnail to the final answer shown to the user.

---

## Notes on Using These Diagrams

- These diagrams assume **Phase 1 (single video)** scope. In Phase 2 (multi-video), Process 1.0 and the data stores gain a `video_id`/`camera_id` dimension that is already accounted for in the schema (see `CLAUDE.md`, Section 6) — no new processes are needed, only multiplicity of the existing ones.
- If you add new pipeline stages (e.g., anomaly scoring, alerting), extend Level 1 first, then add a corresponding Level 2 decomposition — keep this file as the up-to-date structural reference alongside `ARCHITECTURE.md`.

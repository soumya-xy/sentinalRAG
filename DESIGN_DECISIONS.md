# Design Decisions — SentinelRAG

This document records the *why* behind every major technical and visual decision in this project — not just what was chosen, but what alternatives were considered and rejected. Treat this as binding unless explicitly revisited; if a future change contradicts something here, flag the conflict before proceeding.

---

## Part 1 — Technical / Architecture Decisions

| Area | Decision | Alternatives Considered | Why This Choice |
|---|---|---|---|
| Processing mode | Batch (offline) processing only | Live/real-time RTSP streaming | Streaming infra (buffering, latency budgets, dropped-frame handling) adds engineering surface area disproportionate to project scope. Batch mirrors how real enterprise video-search products (Verkada, Axis) are actually architected — index first, query later. |
| Detection model | Ultralytics **YOLO11** | YOLOv8, YOLO26, RT-DETR | YOLO11 improves small/cluttered-object detection over YOLOv8, which matters for crowded surveillance scenes. YOLO26 (Jan 2026) is newer with thinner community support/documentation — higher risk for a solo, deadline-bound build. RT-DETR has strong accuracy but heavier compute needs without a proportional benefit here. |
| Detection weights | Pretrained COCO weights; light fine-tuning is a stretch goal | Training a custom detector from scratch | COCO already covers the needed classes (person, vehicle, bag). Training from scratch demands large labeled datasets and compute with no proportional accuracy gain at this scope. |
| Captioning model | **Gemini 2.0 Flash vision (API)** for the no-local-GPU path; Qwen2.5-VL remains the local target | Qwen2.5-VL locally, BLIP-2, LLaVA | The original local choice is still Qwen2.5-VL, but Phase 1 has no vLLM/cloud GPU. Gemini is multimodal, already used for answers, and unblocks a real (non-demo) captioner without a local 7B VLM. Switch `VLM_PROVIDER=qwen` later if a GPU box appears. |
| Captioning trigger strategy | Two-stage: cheap YOLO pass flags relevant frames → expensive VLM captions only those | Run VLM on every sampled frame | Running a multi-billion-parameter VLM on every frame is wasteful and slow. Gating VLM calls behind cheap detection is a deliberate cost/latency optimization worth calling out as a system-design choice, not just a technical shortcut. |
| Captioning fallback | Rule-based template captions if Gemini is unavailable | Requiring VLM captioning from day one | Keeps ingest alive through missing keys, quota errors, or a bad frame. |
| Answer-generation LLM | **Gemini** via LangGraph | Anthropic, OpenAI, local vLLM | The author has a Gemini API key and no local LLM endpoint. Provider stays configurable. |
| Embeddings | Gemini `text-embedding-004` (768-d) by default; BGE-M3 when `EMBEDDING_PROVIDER=local` | BGE-M3 only | Vectors are written into Supabase pgvector. The API embedder avoids a multi-GB CPU download. |
| Vector database | **Supabase pgvector** | ChromaDB, Pinecone, Weaviate | Explicitly adopted so auth, files, rows, and vectors live in one hosted project. ChromaDB is removed. |
| Object storage | **Supabase Storage** | Local `data/` folders | Videos and thumbnails are per-user objects. The laptop only keeps OS temp files during YOLO, then deletes them. |
| Auth | **Supabase Auth** | In-memory JWT demo users | Real accounts; each user_id only reads its own videos/events. |
| Orchestration | **LangGraph** | Raw prompt chaining, LlamaIndex | Consistent with existing framework experience; demonstrates depth in one tool rather than fragmenting effort across frameworks with overlapping purposes. |
| Backend framework | **FastAPI** | Flask, Node/Express | Async-friendly, lightweight, and consistent with prior project stack. |
| Frame sampling | Fixed interval or scene-change detection (OpenCV) | Every-frame processing | Processing every frame is redundant for slowly-changing surveillance footage and multiplies compute cost with little added recall. |
| Build sequencing | Single video → full pipeline first, multi-video/camera second | Building multi-camera support immediately | Prevents premature complexity. The schema is designed up front (`video_id`/`camera_id` present from day one) so Phase 2 is additive, not a rewrite. |

---

## Part 2 — Visual / UI Design Decisions

### 2.1 What we are deliberately avoiding

Default "AI-generated app" visual tells were identified and explicitly rejected for this project:
- Purple/blue/orange gradient combinations (the default SaaS-template palette seen everywhere)
- Warm cream background + terracotta accent (a different but equally common generic AI-tool look)
- Generic rounded "SaaS card kit" — identical border-radius on every element, soft grey drop-shadows on every card, decorative gradient washes
- All-caps tracked-out labels, middle-dot-separated meta strings, arrow-suffixed button text — template chrome that says nothing about *this* product

None of these are wrong in general — they're simply defaults, and defaults don't fit a project whose entire value proposition is close observation and precision (surveillance analysis), not generic productivity software.

### 2.2 Grounding the palette in the subject matter

The visual language should come from the actual world this tool lives in: **control rooms, night-vision optics, and analog security signage** — not from generic SaaS dashboard conventions. This is deliberately chosen because:
- Dark, desaturated bases are also the accepted, functional standard for data-dense monitoring interfaces (used by Linear, Vercel, Supabase for exactly this reason: technical users doing sustained reading benefit from low-glare surfaces).
- A security/surveillance product should visually read as *serious, precise, and low-noise* — closer to an operations console than a marketing site.

### 2.3 Chosen Palette

| Role | Hex | Rationale |
|---|---|---|
| Base background | `#0D1210` | Near-black, desaturated toward green rather than blue — evokes night-vision optics and low-light monitoring environments without being a literal neon "hacker" cliché. Avoids pure `#000000`, which causes harsh contrast and OLED smearing. |
| Elevated surface (cards/panels) | `#161C1A` | A step up from base for layering (event cards, panels, modals) — maintains the same desaturated-green undertone so elevation reads as depth, not a different theme. |
| Border / divider | `#2A322E` | Low-contrast structural lines — present but never competing with content. |
| Text — primary | `#E8E6DE` | A warm off-white rather than clinical pure white — easier on the eyes for long monitoring sessions, and warmer than the sterile white common in generic dashboards. |
| Text — secondary/muted | `#8B9490` | For timestamps, metadata, secondary labels — desaturated to sit quietly behind primary content. |
| Accent — active/detected state | `#8FA888` (muted sage/moss green) | A deliberately *desaturated* nod to phosphor night-vision green — used for "event detected," active retrieval highlights, success states. Muted rather than neon so it reads as considered, not decorative. |
| Accent — warning | `#C98A3D` (muted amber/ochre) | Drawn from sodium-vapor security lighting and analog hazard signage — used sparingly for medium-priority flags (e.g., low-confidence detection, unresolved query). |
| Accent — critical | `#B5533C` (muted brick/rust red) | Deliberately not a bright alarm red — closer to worn warning tape or rust than a UI-kit red — used only for genuine critical states (failed processing, high-confidence security-relevant event). |

**Explicitly rejected:** saturated purple, cobalt/electric blue, and stock "CTA orange" — these were ruled out specifically because they are the most common defaults in generic AI-tool and SaaS UI right now and carry no connection to this project's subject matter.

### 2.4 Typography

- **One typeface family** for both display and body text, at minimum two clearly distinct weights (regular/medium for body, semibold/bold for headings) — avoid mixing an unrelated display face with a separate body face unless a clear rationale emerges during build.
- Favor a **monospaced or slab-leaning face for data-dense elements** (timestamps, confidence scores, event IDs) to visually separate "system data" from "narrative text" (captions, answers) — this is a functional distinction, not decoration, and doubles as a subtle nod to terminal/console aesthetics without going full "hacker green terminal" cliché.
- Line lengths under ~80 characters for readable text blocks (answer text, event descriptions).

### 2.5 Layout principles

- **Left-aligned, console-style layout** — not centered marketing-page layout. This is a working tool, not a landing page; alignment should support scanning dense information quickly.
- **One deliberate area of visual weight**: the query/answer interaction (where the user asks a question and sees the grounded answer) is the single "hero" moment. Everything else — video list, event timeline, thumbnails — stays quiet and structurally consistent so the answer interaction stands out.
- Avoid decorative gradients entirely; use flat, solid surfaces at each elevation level.
- Numbered markers (01/02/03 style) are used only where content is a genuine sequence (e.g., the pipeline stages in documentation diagrams) — not applied to UI sections that aren't sequential.

### 2.6 Motion

- Motion is reserved for **direct responses to user action**: a query being submitted, results appearing, a video finishing processing. No scroll-triggered fade-ins or per-card hover animations applied uniformly — those are generic template tells and add visual noise to a tool meant for focused reading.

---

## 3. Maintenance Note

If any decision in this file changes, update it here first, then propagate to `CLAUDE.md`, `ARCHITECTURE.md`, and any frontend theme/config files (e.g., Tailwind config, CSS variables) so a single source of truth is preserved.

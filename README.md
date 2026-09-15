# SentinelRAG

Video-surveillance RAG: upload recorded CCTV, ask natural-language questions, get answers grounded in a timestamp, camera/video ID, and cited frame.

Phase 1 is a single-video vertical slice. The UI and API contracts are complete. YOLO11, Qwen2.5-VL, ChromaDB, and LangGraph are **stubbed** behind stable interfaces so inference can be wired later without rewriting the frontend.

## Setup

```powershell
copy env.example .env
```

Fill keys in `.env` when you add real models. The app runs with the defaults for a local demo.

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

Demo login: `demo@sentinelrag.dev` / `demo1234`

### Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

UI: http://localhost:3000 (CORS origin matches `ALLOWED_ORIGINS` in `env.example`).

```powershell
npm run build
```

### Tests

```powershell
cd backend
python -m pytest
```

## Stubbed vs real

| Surface | Status |
|---|---|
| Auth (register / login / logout / me) | Mock JWT + in-memory users |
| Video upload + processing status | File saved; stages advance on a timer, then mock events are materialized |
| Frame sampling / YOLO11 / caption / Chroma index | Typed pipeline modules, mock bodies, `NotImplemented` real paths |
| Query + citations | Keyword retrieval + LangGraph-shaped compose/cite stub |
| Frontend `src/lib/api` | Single swap point for real HTTP behavior |

Processing time is `MOCK_PROCESSING_SECONDS` (default 9) so the ingest progress UI is visible.

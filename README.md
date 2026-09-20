# SentinelRAG

Video-surveillance RAG: upload recorded CCTV, ask natural-language questions, get answers grounded in a timestamp, camera/video ID, and a cited frame.

**Nothing user-specific is stored on this machine.** Auth, videos, thumbnails, event rows, and vectors live in **Supabase**. The API only writes OS temp files while YOLO runs, then deletes them.

## What you must paste into `.env`

Create a Supabase project, then copy `env.example` to `.env` and fill:

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Project Settings → API → Project URL (`https://xxxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | Project Settings → API → `anon` `public` key |
| `SUPABASE_SERVICE_ROLE_KEY` | Project Settings → API → `service_role` key (**secret** — backend only) |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |

Optional: `SUPABASE_JWT_SECRET` (Settings → API → JWT Secret). The backend uses `auth.get_user` so this is not required.

You do **not** need a separate database URL. The service role key can read/write Postgres and Storage.

## One-time Supabase setup

1. Auth → Providers → Email: turn **Confirm email** **off** while you develop (otherwise register returns no session).
2. SQL Editor: run [`supabase/migrations/001_init.sql`](supabase/migrations/001_init.sql). If that file was already applied earlier, also run [`supabase/migrations/002_retrieval_and_event_quality.sql`](supabase/migrations/002_retrieval_and_event_quality.sql), [`supabase/migrations/003_add_hnsw_index.sql`](supabase/migrations/003_add_hnsw_index.sql), and [`supabase/migrations/004_embedding_model.sql`](supabase/migrations/004_embedding_model.sql). That creates:
   - `vector` extension
   - `videos` and `events` tables (`events.embedding vector(768)`)
   - HNSW index on `events.embedding` (`vector_cosine_ops`)
   - `match_events(...)` RPC for similarity search
   - private buckets `videos` and `thumbnails`
   - RLS so each `auth.uid()` only sees its own rows/objects
3. Confirm Storage shows buckets `videos` and `thumbnails`.

The backend uses the **service role**, which bypasses RLS. Policies are there so a leaked anon key cannot read another user's files.

## Run

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:3000 and **register** a real account (no demo user).

Upload a short clip first (30–90s). YOLO still runs on your CPU/GPU.

```powershell
cd backend
python -m pytest
```

Tests force an empty Supabase config and use an in-memory catalog. They never write `data/`.

## What lives where

| Data | Location |
|---|---|
| Users / passwords / sessions | Supabase Auth |
| Uploaded videos | Supabase Storage `videos/{user_id}/{video_id}.mp4` |
| Event thumbnails | Supabase Storage `thumbnails/{user_id}/{video_id}/{event_id}.jpg` |
| Video status + event captions | Supabase table `videos` / `events` |
| Caption vectors | `events.embedding` (pgvector, 768-d Gemini embeddings) plus `embedding_model` |
| YOLO weights | Local `yolo11n.pt` only (model file, not user data) |
| Sampled frames | OS temp dir, deleted when ingest finishes |

## Pipeline

Upload → OpenCV sample (temp) → YOLO11 → event windows → Gemini captions → Gemini embeddings → pgvector → LangGraph answer with citations.

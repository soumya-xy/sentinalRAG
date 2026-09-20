-- Apply this if 001_init.sql was already run. Safe to re-run.
-- SHA-256 of uploaded bytes so a completed ingest can be reused instead of reprocessed.

alter table public.videos
  add column if not exists content_hash text;

create index if not exists videos_user_content_hash_idx
  on public.videos (user_id, content_hash);

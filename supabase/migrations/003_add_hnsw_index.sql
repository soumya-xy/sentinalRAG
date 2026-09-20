-- Migration 003: Explicit HNSW Vector Index on events.embedding
-- Configured for cosine distance matching vector_cosine_ops (<=> operator).
-- Enables logarithmic approximate nearest neighbor (ANN) vector search, replacing O(N) sequential scans.

drop index if exists public.events_embedding_hnsw_idx;
drop index if exists public.events_embedding_hnsw;

create index events_embedding_hnsw_idx
  on public.events
  using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

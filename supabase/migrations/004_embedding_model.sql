-- Apply this if 001_init.sql was already run. Safe to re-run.
-- Records which embedder produced events.embedding so a later model swap is visible.

alter table public.events
  add column if not exists embedding_model text;

alter table public.events
  add column if not exists embedding_model_version text;

update public.events
  set embedding_model = 'text-embedding-004'
  where embedding_model is null or btrim(embedding_model) = '';

alter table public.events
  alter column embedding_model set default 'text-embedding-004';

alter table public.events
  alter column embedding_model set not null;

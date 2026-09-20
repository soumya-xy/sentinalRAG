-- SentinelRAG — run this in the Supabase SQL editor (or `supabase db push`).
-- Enables pgvector, video/event tables, similarity RPC, and private storage buckets.

create extension if not exists vector;

create table if not exists public.videos (
  video_id text primary key,
  user_id uuid not null,
  camera_id text not null,
  filename text not null,
  original_filename text not null,
  storage_path text not null,
  status text not null,
  duration_seconds double precision,
  size_bytes bigint not null default 0,
  error text,
  events_materialized boolean not null default false,
  current_stage text,
  overall_progress double precision not null default 0,
  stage_states jsonb not null default '{}'::jsonb,
  stage_progress jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists videos_user_id_idx on public.videos (user_id);
create index if not exists videos_created_at_idx on public.videos (created_at desc);

create table if not exists public.events (
  event_id text primary key,
  video_id text not null references public.videos (video_id) on delete cascade,
  user_id uuid not null,
  camera_id text not null,
  start_timestamp text not null,
  end_timestamp text not null,
  caption text not null,
  detected_classes text[] not null default '{}',
  bounding_boxes jsonb not null default '[]'::jsonb,
  thumbnail_path text not null,
  thumbnail_url text,
  confidence_score double precision not null,
  caption_source text,
  object_count integer not null default 1,
  embedding_model text not null default 'text-embedding-004',
  embedding_model_version text,
  embedding vector(768),
  created_at timestamptz not null default now()
);

create index if not exists events_video_id_idx on public.events (video_id);
create index if not exists events_user_id_idx on public.events (user_id);

drop index if exists events_embedding_hnsw;
create index events_embedding_hnsw
  on public.events
  using hnsw (embedding vector_cosine_ops);

drop function if exists public.match_events(vector, text, int);
drop function if exists public.match_events(vector, text, int, uuid);

create or replace function public.match_events(
  query_embedding vector(768),
  filter_video_id text,
  match_count int default 8,
  filter_user_id uuid default null
)
returns table (
  event_id text,
  similarity float
)
language sql
stable
as $$
  select
    e.event_id,
    (1 - (e.embedding <=> query_embedding))::float as similarity
  from public.events e
  where e.video_id = filter_video_id
    and e.embedding is not null
    and (filter_user_id is null or e.user_id = filter_user_id)
  order by e.embedding <=> query_embedding
  limit match_count;
$$;

alter table public.videos enable row level security;
alter table public.events enable row level security;

drop policy if exists "users read own videos" on public.videos;
create policy "users read own videos"
  on public.videos for select
  using (auth.uid() = user_id);

drop policy if exists "users write own videos" on public.videos;
create policy "users write own videos"
  on public.videos for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "users read own events" on public.events;
create policy "users read own events"
  on public.events for select
  using (auth.uid() = user_id);

drop policy if exists "users write own events" on public.events;
create policy "users write own events"
  on public.events for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

insert into storage.buckets (id, name, public, file_size_limit)
values
  ('videos', 'videos', false, 524288000),
  ('thumbnails', 'thumbnails', false, 10485760)
on conflict (id) do nothing;

drop policy if exists "users read own video objects" on storage.objects;
create policy "users read own video objects"
  on storage.objects for select
  using (
    bucket_id in ('videos', 'thumbnails')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

drop policy if exists "users write own video objects" on storage.objects;
create policy "users write own video objects"
  on storage.objects for all
  using (
    bucket_id in ('videos', 'thumbnails')
    and (storage.foldername(name))[1] = auth.uid()::text
  )
  with check (
    bucket_id in ('videos', 'thumbnails')
    and (storage.foldername(name))[1] = auth.uid()::text
  );

grant execute on function public.match_events(vector, text, int, uuid) to anon, authenticated, service_role;

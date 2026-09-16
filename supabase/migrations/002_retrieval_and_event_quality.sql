-- Apply this if 001_init.sql was already run on the project.
-- Safe to re-run. Adds object_count and scopes match_events by user_id.

alter table public.events
  add column if not exists object_count integer not null default 1;

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

grant execute on function public.match_events(vector, text, int, uuid) to anon, authenticated, service_role;

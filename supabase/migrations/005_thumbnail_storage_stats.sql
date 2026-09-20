-- Apply this if 001_init.sql was already run. Safe to re-run.
-- Size stats for confirming events rows no longer hold inlined thumbnail bytes.

create or replace function public.events_storage_stats()
returns table (
  heap_bytes bigint,
  table_plus_toast_bytes bigint,
  indexes_bytes bigint,
  total_bytes bigint,
  event_count bigint,
  inline_thumbnail_count bigint,
  persisted_url_count bigint,
  avg_thumbnail_path_chars double precision,
  avg_thumbnail_url_chars double precision
)
language sql
stable
security definer
set search_path = public, pg_catalog
as $$
  select
    pg_relation_size('public.events')::bigint,
    pg_table_size('public.events')::bigint,
    pg_indexes_size('public.events')::bigint,
    pg_total_relation_size('public.events')::bigint,
    (select count(*) from public.events),
    (
      select count(*)
      from public.events
      where thumbnail_path like 'data:%'
         or coalesce(thumbnail_url, '') like 'data:%'
         or thumbnail_path like '%base64,%'
         or coalesce(thumbnail_url, '') like '%base64,%'
         or length(thumbnail_path) > 400
         or length(coalesce(thumbnail_url, '')) > 400
    ),
    (
      select count(*)
      from public.events
      where thumbnail_url is not null and btrim(thumbnail_url) <> ''
    ),
    (select avg(length(thumbnail_path))::double precision from public.events),
    (select avg(length(coalesce(thumbnail_url, '')))::double precision from public.events);
$$;

revoke all on function public.events_storage_stats() from public;
grant execute on function public.events_storage_stats() to service_role;

create or replace function public.list_inline_thumbnail_events()
returns table (
  event_id text,
  video_id text,
  user_id uuid,
  thumbnail_path text,
  thumbnail_url text
)
language sql
stable
security definer
set search_path = public
as $$
  select
    e.event_id,
    e.video_id,
    e.user_id,
    e.thumbnail_path,
    e.thumbnail_url
  from public.events e
  where e.thumbnail_path like 'data:%'
     or coalesce(e.thumbnail_url, '') like 'data:%'
     or e.thumbnail_path like '%base64,%'
     or coalesce(e.thumbnail_url, '') like '%base64,%'
     or length(e.thumbnail_path) > 400
     or length(coalesce(e.thumbnail_url, '')) > 400;
$$;

revoke all on function public.list_inline_thumbnail_events() from public;
grant execute on function public.list_inline_thumbnail_events() to service_role;

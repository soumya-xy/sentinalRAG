from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_anon_client():
    settings = get_settings()
    if not settings.supabase_enabled:
        raise RuntimeError("Supabase is not configured (SUPABASE_URL / keys missing).")
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache(maxsize=1)
def get_admin_client():
    settings = get_settings()
    if not settings.supabase_enabled:
        raise RuntimeError("Supabase is not configured (SUPABASE_URL / keys missing).")
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def reset_supabase_clients() -> None:
    get_anon_client.cache_clear()
    get_admin_client.cache_clear()

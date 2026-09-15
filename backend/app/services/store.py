from __future__ import annotations

from app.core.config import get_settings
from app.services.catalog_types import (
    PIPELINE_STAGES,
    STAGE_KEYS,
    CaptionMode,
    UserRecord,
    VideoInternal,
    now_utc,
)
from app.services.memory_store import MemoryCatalog

__all__ = [
    "PIPELINE_STAGES",
    "STAGE_KEYS",
    "CaptionMode",
    "UserRecord",
    "VideoInternal",
    "now_utc",
    "store",
    "configure_store",
]


class StoreProxy:
    def __init__(self) -> None:
        self.impl = MemoryCatalog()

    def configure(self) -> None:
        if get_settings().supabase_enabled:
            from app.services.supabase_catalog import SupabaseCatalog

            self.impl = SupabaseCatalog()
        else:
            self.impl = MemoryCatalog()

    def __getattr__(self, name: str):
        return getattr(self.impl, name)


store = StoreProxy()


def configure_store() -> None:
    store.configure()
    if not get_settings().supabase_enabled:
        store.seed_demo_user()

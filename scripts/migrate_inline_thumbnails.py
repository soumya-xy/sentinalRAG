"""One-time: move in-row thumbnail bytes into Supabase Storage.

Current ingest already stores JPEG/SVG files in the private `thumbnails` bucket
and only a storage key in `events.thumbnail_path`. This script repairs leftover
rows that still hold `data:image/...;base64,...` (or raw base64) in
`thumbnail_path` / `thumbnail_url`, then clears persisted URLs.

Prints `pg_total_relation_size('public.events')` before and after via
`events_storage_stats()` (apply `supabase/migrations/005_thumbnail_storage_stats.sql`
first).

Usage (repo root, `.env` loaded by Settings):

  python scripts/migrate_inline_thumbnails.py
  python scripts/migrate_inline_thumbnails.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.services.object_storage import (  # noqa: E402
    decode_inline_image,
    looks_like_inline_image,
    thumbnail_object_key,
    upload_bytes,
)
from app.services.supabase_client import get_admin_client  # noqa: E402


def _fmt_bytes(value: object) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    if number < 1024:
        return f"{number} B"
    if number < 1024 * 1024:
        return f"{number / 1024:.1f} KiB"
    return f"{number / (1024 * 1024):.2f} MiB"


def _fetch_stats(client) -> dict | None:
    try:
        result = client.rpc("events_storage_stats").execute()
    except Exception as exc:
        print(f"events_storage_stats RPC unavailable ({exc}). Apply 005_thumbnail_storage_stats.sql.")
        return None
    rows = result.data or []
    if not rows:
        return None
    return rows[0] if isinstance(rows[0], dict) else None


def _scan_column_metrics(client) -> dict:
    result = (
        client.table("events")
        .select("event_id,thumbnail_path,thumbnail_url")
        .execute()
    )
    rows = result.data or []
    path_lens = [len(row.get("thumbnail_path") or "") for row in rows]
    url_lens = [len(row.get("thumbnail_url") or "") for row in rows]
    inline = sum(
        1
        for row in rows
        if _inline_source(row.get("thumbnail_path"), row.get("thumbnail_url"))
    )
    return {
        "event_count": len(rows),
        "inline_thumbnail_count": inline,
        "persisted_url_count": sum(1 for row in rows if row.get("thumbnail_url")),
        "thumbnail_path_chars": sum(path_lens),
        "thumbnail_url_chars": sum(url_lens),
        "max_thumbnail_path_chars": max(path_lens, default=0),
        "max_thumbnail_url_chars": max(url_lens, default=0),
    }


def _print_stats(label: str, stats: dict | None, scanned: dict | None = None) -> None:
    print(f"\n=== {label} ===")
    if scanned:
        print(f"  event_count              {scanned.get('event_count')}")
        print(f"  inline_thumbnail_count   {scanned.get('inline_thumbnail_count')}")
        print(f"  persisted_url_count      {scanned.get('persisted_url_count')}")
        print(f"  thumbnail_path chars     {scanned.get('thumbnail_path_chars')}")
        print(f"  thumbnail_url chars      {scanned.get('thumbnail_url_chars')}")
        print(f"  max thumbnail_path chars {scanned.get('max_thumbnail_path_chars')}")
        print(f"  max thumbnail_url chars  {scanned.get('max_thumbnail_url_chars')}")
    if not stats:
        if not scanned:
            print("  (no stats)")
        return
    print(f"  heap                     {_fmt_bytes(stats.get('heap_bytes'))}")
    print(f"  table + toast            {_fmt_bytes(stats.get('table_plus_toast_bytes'))}")
    print(f"  indexes                  {_fmt_bytes(stats.get('indexes_bytes'))}")
    print(f"  pg_total_relation_size   {_fmt_bytes(stats.get('total_bytes'))}")
    print(f"  avg thumbnail_path chars {stats.get('avg_thumbnail_path_chars')}")
    print(f"  avg thumbnail_url chars  {stats.get('avg_thumbnail_url_chars')}")


def _inline_source(path: str | None, url: str | None) -> str | None:
    if looks_like_inline_image(path):
        return path
    if looks_like_inline_image(url):
        return url
    return None


def _list_inline_rows(client) -> list[dict]:
    try:
        result = client.rpc("list_inline_thumbnail_events").execute()
        return list(result.data or [])
    except Exception:
        print("list_inline_thumbnail_events RPC unavailable; scanning events columns.")
        result = (
            client.table("events")
            .select("event_id,video_id,user_id,thumbnail_path,thumbnail_url")
            .execute()
        )
        rows = []
        for row in result.data or []:
            if _inline_source(row.get("thumbnail_path"), row.get("thumbnail_url")):
                rows.append(row)
        return rows


def _migrate_row(client, row: dict, bucket: str, dry_run: bool) -> bool:
    event_id = row["event_id"]
    video_id = row["video_id"]
    user_id = str(row["user_id"])
    source = _inline_source(row.get("thumbnail_path"), row.get("thumbnail_url"))
    if not source:
        return False
    raw, suffix, content_type = decode_inline_image(source)
    key = thumbnail_object_key(user_id, video_id, f"{event_id}{suffix}")
    print(f"  {event_id}: {len(source)} chars -> {key} ({len(raw)} bytes, {content_type})")
    if dry_run:
        return True
    upload_bytes(bucket, key, raw, content_type)
    client.table("events").update({"thumbnail_path": key, "thumbnail_url": None}).eq(
        "event_id", event_id
    ).execute()
    return True


def _clear_persisted_urls(client, dry_run: bool) -> int:
    result = (
        client.table("events")
        .select("event_id,thumbnail_url")
        .not_.is_("thumbnail_url", "null")
        .execute()
    )
    ids = [
        row["event_id"]
        for row in (result.data or [])
        if row.get("thumbnail_url")
    ]
    if not ids:
        return 0
    print(f"  clearing persisted thumbnail_url on {len(ids)} row(s)")
    if dry_run:
        return len(ids)
    for event_id in ids:
        client.table("events").update({"thumbnail_url": None}).eq("event_id", event_id).execute()
    return len(ids)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.supabase_enabled:
        print("Supabase is not configured. Set SUPABASE_URL and service-role keys in .env.")
        return 1

    client = get_admin_client()
    before_scan = _scan_column_metrics(client)
    before = _fetch_stats(client)
    _print_stats("before", before, before_scan)

    rows = _list_inline_rows(client)
    print(f"\nInline/base64 candidate rows: {len(rows)}")
    moved = 0
    failed = 0
    for row in rows:
        try:
            if _migrate_row(client, row, settings.supabase_thumbnails_bucket, args.dry_run):
                moved += 1
        except Exception as exc:
            failed += 1
            print(f"  {row.get('event_id')}: failed ({exc})")

    cleared = _clear_persisted_urls(client, args.dry_run)
    after_scan = _scan_column_metrics(client)
    after = _fetch_stats(client)
    _print_stats("after", after, after_scan)

    if before and after and before.get("total_bytes") is not None and after.get("total_bytes") is not None:
        delta = int(before["total_bytes"]) - int(after["total_bytes"])
        print(f"\npg_total_relation_size delta: {_fmt_bytes(delta)} smaller after migration")
    path_delta = int(before_scan["thumbnail_path_chars"]) - int(after_scan["thumbnail_path_chars"])
    url_delta = int(before_scan["thumbnail_url_chars"]) - int(after_scan["thumbnail_url_chars"])
    print(f"thumbnail_path chars delta: {path_delta}")
    print(f"thumbnail_url chars delta:  {url_delta}")

    print(f"\nmoved={moved} failed={failed} cleared_urls={cleared} dry_run={args.dry_run}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

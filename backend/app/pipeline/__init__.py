"""Batch ingest pipeline stages (temp files only; persist in Supabase)."""

from app.pipeline.runner import run_ingest_pipeline

__all__ = ["run_ingest_pipeline"]

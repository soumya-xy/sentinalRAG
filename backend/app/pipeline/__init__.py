"""Batch ingest pipeline stages.

Each module exposes a typed interface. Bodies are mocks with TODOs so
YOLO11 / Qwen2.5-VL / Chroma can be swapped in without changing routers.
"""

from app.pipeline.runner import run_ingest_pipeline

__all__ = ["run_ingest_pipeline"]

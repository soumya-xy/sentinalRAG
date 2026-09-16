"""Lazy, process-wide handles for YOLO and embeddings. No local vector DB."""

from __future__ import annotations

import logging
import threading
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("sentinelrag.ml")

_lock = threading.Lock()
_yolo: Any = None
_yolo_device: str | None = None
_local_embedder: Any = None
_gemini_embedder: Any = None


def resolve_yolo_device(requested: str) -> str:
    wanted = (requested or "auto").strip().lower()
    cuda_ok = False
    try:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
    except Exception:
        cuda_ok = False

    if wanted in {"auto", "cuda"} and cuda_ok:
        return "0"
    if wanted == "mps":
        return "mps"
    return "cpu"


def get_yolo():
    global _yolo, _yolo_device
    if _yolo is not None:
        return _yolo, _yolo_device
    with _lock:
        if _yolo is None:
            from ultralytics import YOLO

            settings = get_settings()
            weights = settings.resolve_yolo_weights()
            _yolo_device = resolve_yolo_device(settings.yolo_device)
            logger.info("Loading YOLO11 weights=%s device=%s", weights, _yolo_device)
            _yolo = YOLO(weights)
        return _yolo, _yolo_device


def _local_embedder_model():
    global _local_embedder
    if _local_embedder is not None:
        return _local_embedder
    with _lock:
        if _local_embedder is None:
            from sentence_transformers import SentenceTransformer

            settings = get_settings()
            logger.info("Loading local embedder %s", settings.embedding_model_name)
            _local_embedder = SentenceTransformer(settings.embedding_model_name)
        return _local_embedder


def _gemini_embedder_model():
    global _gemini_embedder
    if _gemini_embedder is not None:
        return _gemini_embedder
    with _lock:
        if _gemini_embedder is None:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            settings = get_settings()
            if not settings.google_api_key:
                raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google")
            model_name = settings.google_embedding_model.replace("models/", "")
            logger.info("Using Gemini embeddings model=%s", model_name)
            _gemini_embedder = GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=settings.google_api_key,
            )
        return _gemini_embedder


def _require_dim(vec: list[float], target_dim: int) -> list[float]:
    if len(vec) == target_dim:
        return vec
    raise RuntimeError(
        f"Embedding dimension {len(vec)} does not match pgvector size {target_dim}. "
        "Do not mix embedding providers against the same events table."
    )


def _embed_with_retry(operation, *, attempts: int = 3):
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            logger.warning("Embedding attempt %s/%s failed: %s", attempt + 1, attempts, exc)
    assert last_error is not None
    raise last_error


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    settings = get_settings()
    target_dim = settings.embedding_dimensions
    provider = (settings.embedding_provider or "google").lower()

    if provider == "google":
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google")
        raw_embeddings = _embed_with_retry(lambda: _gemini_embedder_model().embed_documents(texts))
    else:
        raw_embeddings = _local_embedder_model().encode(texts).tolist()

    return [_require_dim(vec, target_dim) for vec in raw_embeddings]


def embed_query(text: str) -> list[float]:
    settings = get_settings()
    target_dim = settings.embedding_dimensions
    provider = (settings.embedding_provider or "google").lower()

    if provider == "google":
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google")
        raw_vec = _embed_with_retry(lambda: _gemini_embedder_model().embed_query(text))
    else:
        raw_vec = _local_embedder_model().encode([text])[0].tolist()

    return _require_dim(raw_vec, target_dim)


def reset_ml_handles() -> None:
    global _yolo, _yolo_device, _local_embedder, _gemini_embedder
    with _lock:
        _yolo = None
        _yolo_device = None
        _local_embedder = None
        _gemini_embedder = None

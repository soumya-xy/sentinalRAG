import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, events, health, media, query, videos
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.services.store import configure_store


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging()
    configure_store()
    if settings.supabase_enabled:
        logging.getLogger("sentinelrag").info("Catalog backend: Supabase + pgvector")
    else:
        logging.getLogger("sentinelrag").warning(
            "Supabase is not configured; using in-memory catalog (tests / local fallback only)."
        )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="SentinelRAG",
        description="Phase 1 video-surveillance RAG API. YOLO11 ingest, Gemini captions/answers, Supabase pgvector.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Query-ID"],
    )
    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(videos.router)
    application.include_router(events.router)
    application.include_router(query.router)
    application.include_router(media.router)
    return application


app = create_app()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, events, health, media, query, videos
from app.core.config import get_settings
from app.services.storage import ensure_storage_dirs
from app.services.store import store


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    ensure_storage_dirs(settings)
    store.seed_demo_user()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="SentinelRAG",
        description="Phase 1 video-surveillance RAG API. Pipeline stages are stubbed; contracts are stable.",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(videos.router)
    application.include_router(events.router)
    application.include_router(query.router)
    application.include_router(media.router)
    return application


app = create_app()

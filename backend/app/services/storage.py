from pathlib import Path

from app.core.config import Settings, get_settings


def ensure_storage_dirs(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    for directory in (
        settings.videos_dir,
        settings.thumbnails_dir,
        settings.frames_dir,
        settings.chroma_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def video_file_path(video_id: str, suffix: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return settings.videos_dir / f"{video_id}{safe_suffix}"


def thumbnail_file_path(video_id: str, event_id: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    directory = settings.thumbnails_dir / video_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{event_id}.svg"


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

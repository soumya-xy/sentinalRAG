from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment keys match `env.example` at the repository root."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    video_storage_path: str = "./data/videos"
    thumbnail_storage_path: str = "./data/thumbnails"
    frame_cache_path: str = "./data/frames"

    frame_sample_interval_seconds: float = 1.5
    use_scene_change_detection: bool = False

    yolo_model_name: str = "yolo11n.pt"
    yolo_confidence_threshold: float = 0.4
    yolo_device: str = "cuda"

    vlm_model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    vlm_inference_mode: str = "local"
    vlm_inference_endpoint: str = ""
    vlm_use_rule_based_fallback: bool = True
    huggingface_token: str = ""

    embedding_model_name: str = "BAAI/bge-m3"

    chroma_mode: str = "local"
    chroma_db_path: str = "./data/chroma"
    chroma_host: str = ""
    chroma_port: str = ""
    chroma_collection_name: str = "sentinelrag_events"

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"
    local_llm_endpoint: str = ""
    local_llm_model_name: str = ""

    jwt_secret_key: str = ""
    jwt_expiry_minutes: int = 60

    allowed_origins: str = "http://localhost:3000"

    mock_processing_seconds: float = Field(default=9.0)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def jwt_secret(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key
        return "sentinelrag-dev-jwt-secret-change-me"

    def resolve_path(self, raw: str) -> Path:
        path = Path(raw)
        if path.is_absolute():
            return path
        return (REPO_ROOT / path).resolve()

    @property
    def videos_dir(self) -> Path:
        return self.resolve_path(self.video_storage_path)

    @property
    def thumbnails_dir(self) -> Path:
        return self.resolve_path(self.thumbnail_storage_path)

    @property
    def frames_dir(self) -> Path:
        return self.resolve_path(self.frame_cache_path)

    @property
    def chroma_dir(self) -> Path:
        return self.resolve_path(self.chroma_db_path)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()

from functools import lru_cache
from pathlib import Path

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

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_videos_bucket: str = "videos"
    supabase_thumbnails_bucket: str = "thumbnails"

    frame_sample_interval_seconds: float = 0.8
    use_scene_change_detection: bool = False
    event_gap_seconds: float = 4.0
    event_min_box_area: float = 400.0
    event_iou_min: float = 0.25

    retrieval_top_k: int = 3
    retrieval_candidate_k: int = 8
    retrieval_min_similarity: float = 0.48
    retrieval_vector_weight: float = 0.60
    retrieval_lexical_weight: float = 0.25
    retrieval_class_weight: float = 0.10
    retrieval_confidence_weight: float = 0.05

    yolo_model_name: str = "yolo11n.pt"
    yolo_confidence_threshold: float = 0.4
    yolo_device: str = "auto"
    yolo_class_filter: str = (
        "person,bicycle,car,motorcycle,bus,truck,backpack,handbag,suitcase,dog,cat"
    )

    vlm_provider: str = "gemini"
    vlm_model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    vlm_inference_mode: str = "api"
    vlm_inference_endpoint: str = ""
    vlm_use_rule_based_fallback: bool = False
    huggingface_token: str = ""

    embedding_provider: str = "google"
    embedding_model_name: str = "BAAI/bge-m3"
    google_embedding_model: str = "text-embedding-004"
    embedding_dimensions: int = 768

    llm_provider: str = "google"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash"
    local_llm_endpoint: str = ""
    local_llm_model_name: str = ""

    jwt_secret_key: str = ""
    jwt_expiry_minutes: int = 60

    allowed_origins: str = "http://localhost:3000"

    ingest_in_background: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def jwt_secret(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key
        return "sentinelrag-dev-jwt-secret-change-me"

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key and self.supabase_service_role_key)

    @property
    def yolo_allowed_classes(self) -> set[str]:
        return {item.strip() for item in self.yolo_class_filter.split(",") if item.strip()}

    def resolve_yolo_weights(self) -> str:
        name = self.yolo_model_name
        for candidate in (BACKEND_ROOT / name, REPO_ROOT / name, Path(name)):
            if candidate.is_file():
                return str(candidate.resolve())
        return name


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()

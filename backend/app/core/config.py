from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    database_url: str = "sqlite:///./data/app.db"

    jwt_secret: str = Field(default="dev-only-insecure-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    profile_retention_days: int = 30
    chat_retention_days: int = 30

    rate_limit_default: str = "60/minute"
    rate_limit_chat: str = "20/minute"

    chroma_path: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_backend: str = "fastembed"  # fastembed | hashing (offline fallback)
    embedding_cache_dir: str = "./data/models"
    retrieval_min_score: float = 0.25
    chunk_size: int = 900
    chunk_overlap: int = 150

    llm_provider: str = "groq"  # groq | openai_compatible | ollama | none
    llm_model: str = "openai/gpt-oss-120b"  # must be in your key's model list (GET /openai/v1/models)
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_timeout_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and settings.jwt_secret.startswith("dev-only"):
        raise RuntimeError("JWT_SECRET must be set to a strong random value in production")
    return settings

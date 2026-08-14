from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vidora API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"
    database_url: str = "postgresql+asyncpg://vidora:vidora@localhost:5432/vidora"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="change-me-in-development-secret-32", min_length=32)
    download_db_path: str = "backend/data/vidora_downloads.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

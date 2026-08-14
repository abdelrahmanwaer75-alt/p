from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_DEV_JWT_SECRET = "change-me-in-development-secret-32"
INSECURE_JWT_SECRETS = {DEFAULT_DEV_JWT_SECRET, "change-me", "secret", "secret-key", "jwt-secret"}


class Settings(BaseSettings):
    app_name: str = "Vidora API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"
    database_url: str = "sqlite:///./backend/data/vidora_dev.db"
    redis_url: str = "redis://localhost:6379/0"
    download_directory: str = "backend/data/media"
    auto_create_db: bool = True
    jwt_secret: str = Field(default=DEFAULT_DEV_JWT_SECRET, min_length=32)
    jwt_issuer: str = "vidora-api"
    jwt_audience: str = "vidora-client"
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_ttl_seconds: int = Field(default=60 * 60 * 24 * 30, ge=3600, le=60 * 60 * 24 * 365)
    rate_limit_per_minute: int = Field(default=120, ge=10, le=10000)
    auth_rate_limit_per_minute: int = Field(default=60, ge=3, le=1000)
    cors_allow_credentials: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_security(self) -> "Settings":
        if self.environment.lower() in {"production", "prod"}:
            if self.jwt_secret in INSECURE_JWT_SECRETS or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be a strong, non-default secret in production")
            if not self.jwt_issuer.strip() or not self.jwt_audience.strip():
                raise ValueError("JWT issuer and audience must be configured in production")
            if "*" in self.cors_origins or any(origin.startswith("http://") for origin in self.cors_origins):
                raise ValueError("Production CORS origins must be explicit HTTPS origins")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

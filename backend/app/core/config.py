from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_environment: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    database_url: str = Field(min_length=1)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    storage_path: str = "../storage"
    max_upload_size_mb: int = 25
    expiry_approaching_days: int = 90
    expiry_urgent_days: int = 30
    # ── Authentication ────────────────────────────────────────────────────────
    jwt_secret_key: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480
    admin_email: str | None = None
    admin_password: str | None = None
    # ── Notification channels (Phase 4B) ────────────────────────────────────
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_tls: bool = True
    whatsapp_api_token: str | None = None
    whatsapp_phone_id: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

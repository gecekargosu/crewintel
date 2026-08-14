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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

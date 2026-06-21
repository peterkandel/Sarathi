from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "integration_service"
    service_port: int = 8008
    database_url: str = "sqlite+aiosqlite:///./integration_service.db"
    default_retry_attempts: int = 3
    breaker_failure_threshold: int = 3
    breaker_reset_seconds: int = 60


settings = Settings()

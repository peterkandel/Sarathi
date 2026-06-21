from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "application_service"
    service_port: int = 8006
    database_url: str = "postgresql+asyncpg://sarathi:sarathi_password@postgres:5432/sarathi"
    workflow_service_url: str = "http://workflow_service:8004"


settings = Settings()

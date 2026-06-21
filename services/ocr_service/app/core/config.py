from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "ocr_service"
    service_port: int = 8007
    database_url: str = "sqlite+aiosqlite:///./ocr_service.db"
    storage_root: str = "./ocr_storage"
    max_upload_size_bytes: int = 8 * 1024 * 1024
    supported_mime_types: str = "image/jpeg,image/png,image/webp,image/tiff,application/pdf"
    ocr_provider_name: str = "heuristic"
    ocr_engine_name: str = "heuristic"
    ocr_model_version: str = "heuristic-v1"

    @property
    def supported_mime_type_list(self) -> list[str]:
        return [mime_type.strip() for mime_type in self.supported_mime_types.split(",") if mime_type.strip()]


settings = Settings()

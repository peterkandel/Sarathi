from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "notification_service"
    service_port: int = 8005
    database_url: str = "sqlite+aiosqlite:///./notification_service.db"
    default_queue_limit: int = 20


settings = Settings()

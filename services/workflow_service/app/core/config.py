from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "workflow_service"
    service_port: int = 8004
    database_url: str = "postgresql+asyncpg://sarathi:sarathi_password@postgres:5432/sarathi"


settings = Settings()

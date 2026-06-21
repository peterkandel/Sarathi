from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "tax_service"
    service_port: int = 8003
    database_url: str = "sqlite+aiosqlite:///./tax_service.db"
    default_currency: str = "NPR"
    rounding_precision: int = 2


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "identity_service"
    service_port: int = 8001
    database_url: str = "postgresql+asyncpg://sarathi:sarathi_password@postgres:5432/sarathi"
    jwt_issuer: str = "https://auth.sarathi.local"
    jwt_audience: str = "sarathi-api"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    password_reset_ttl_minutes: int = 30


settings = Settings()

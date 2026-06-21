from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/sarathi"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json: bool = False
    include_timestamp: bool = True


class AuthSettings(BaseModel):
    issuer: str = "https://auth.sarathi.local"
    audience: str = "sarathi-api"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    leeway_seconds: int = 0


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    app_name: str = "sarathi-service"
    environment: str = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = Field(default=DatabaseSettings().url)
    database_echo: bool = Field(default=DatabaseSettings().echo)
    database_pool_size: int = Field(default=DatabaseSettings().pool_size)
    database_max_overflow: int = Field(default=DatabaseSettings().max_overflow)
    database_pool_timeout: int = Field(default=DatabaseSettings().pool_timeout)

    log_level: str = Field(default=LoggingSettings().level)
    log_json: bool = Field(default=LoggingSettings().json)

    jwt_issuer: str = Field(default=AuthSettings().issuer)
    jwt_audience: str = Field(default=AuthSettings().audience)
    jwt_secret_key: str = Field(default=AuthSettings().secret_key)
    jwt_algorithm: str = Field(default=AuthSettings().algorithm)
    jwt_leeway_seconds: int = Field(default=AuthSettings().leeway_seconds)

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(
            url=self.database_url,
            echo=self.database_echo,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            pool_timeout=self.database_pool_timeout,
        )

    @property
    def logging(self) -> LoggingSettings:
        return LoggingSettings(level=self.log_level, json=self.log_json)

    @property
    def auth(self) -> AuthSettings:
        return AuthSettings(
            issuer=self.jwt_issuer,
            audience=self.jwt_audience,
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            leeway_seconds=self.jwt_leeway_seconds,
        )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()

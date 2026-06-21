from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mode: str = Field(default="development", validation_alias="AUTH_MODE")
    issuer: str = Field(default="https://auth.sarathi.local", validation_alias="JWT_ISSUER")
    audience: str = Field(default="sarathi-api", validation_alias="JWT_AUDIENCE")
    algorithm: str = Field(default="RS256", validation_alias="JWT_ALGORITHM")
    jwt_public_key: str | None = Field(default=None, validation_alias="JWT_PUBLIC_KEY")
    dev_subject_header: str = Field(default="x-sarathi-subject", validation_alias="AUTH_DEV_SUBJECT_HEADER")
    dev_roles_header: str = Field(default="x-sarathi-roles", validation_alias="AUTH_DEV_ROLES_HEADER")
    dev_agency_header: str = Field(default="x-sarathi-agency-id", validation_alias="AUTH_DEV_AGENCY_HEADER")
    dev_audit_header: str = Field(default="x-sarathi-audit-actor", validation_alias="AUTH_DEV_AUDIT_HEADER")

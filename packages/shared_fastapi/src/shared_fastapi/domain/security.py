from pydantic import BaseModel, Field


class Principal(BaseModel):
    subject: str
    email: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    tenant_id: str | None = None
    agency_id: str | None = None


class TokenClaims(BaseModel):
    sub: str
    iss: str | None = None
    aud: str | list[str] | None = None
    exp: int | None = None
    iat: int | None = None
    nbf: int | None = None
    jti: str | None = None
    scope: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    email: str | None = None
    tenant_id: str | None = None
    agency_id: str | None = None

    def scope_values(self) -> set[str]:
        if not self.scope:
            return set()
        return {value for value in self.scope.split() if value}

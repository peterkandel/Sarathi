from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class APIErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorBody
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    items: list[T] = Field(default_factory=list)
    pagination: PaginationMeta = Field(default_factory=PaginationMeta)
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

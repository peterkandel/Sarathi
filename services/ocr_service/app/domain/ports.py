from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(slots=True)
class UploadedDocument:
    file_name: str
    mime_type: str
    content: bytes
    checksum_sha256: str
    size_bytes: int


@dataclass(slots=True)
class PreprocessedDocument:
    normalized_bytes: bytes
    quality_score: float
    page_count: int
    metadata: dict[str, object]


@dataclass(slots=True)
class OcrTextResult:
    text: str
    confidence: float
    metadata: dict[str, object]


@dataclass(slots=True)
class FieldResult:
    field_name: str
    raw_value: str | None
    normalized_value: str | None
    confidence: float
    validation_status: str
    source_language: str | None = None


@dataclass(slots=True)
class ValidationIssue:
    code: str
    field_name: str | None
    message: str
    severity: str


@dataclass(slots=True)
class ValidationResult:
    status: str
    issues: list[ValidationIssue]


class ObjectStorageProtocol(Protocol):
    async def save(self, storage_key: str, content: bytes, mime_type: str) -> None: ...
    async def load(self, storage_key: str) -> bytes: ...


class OcrProviderProtocol(Protocol):
    async def preprocess(self, document: UploadedDocument) -> PreprocessedDocument: ...
    async def recognize_text(self, document: PreprocessedDocument, document_type_code: str) -> OcrTextResult: ...
    async def extract_fields(self, text_result: OcrTextResult, document_type_code: str) -> Sequence[FieldResult]: ...
    async def validate(self, fields: Sequence[FieldResult], document_type_code: str) -> ValidationResult: ...


class OcrEngineProtocol(OcrProviderProtocol, Protocol):
    pass


class OcrProviderRegistryProtocol(Protocol):
    def get_provider(self, provider_name: str) -> OcrProviderProtocol: ...

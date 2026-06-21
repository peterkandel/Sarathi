from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from app.core.config import settings
from app.domain.ports import FieldResult, OcrProviderProtocol, OcrTextResult, PreprocessedDocument, UploadedDocument, ValidationIssue, ValidationResult


class HeuristicOcrEngine(OcrProviderProtocol):
    async def preprocess(self, document: UploadedDocument) -> PreprocessedDocument:
        content = document.content
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.hex()
        quality_score = self._quality_score(content)
        page_count = max(1, text.count("\f") + 1)
        normalized_bytes = text.strip().encode("utf-8")
        return PreprocessedDocument(normalized_bytes=normalized_bytes, quality_score=quality_score, page_count=page_count, metadata={"content_length": len(content)})

    async def recognize_text(self, document: PreprocessedDocument, document_type_code: str) -> OcrTextResult:
        text = document.normalized_bytes.decode("utf-8", errors="ignore")
        if not text.strip():
            text = f"document_type: {document_type_code}\nfull_name: Unknown Citizen"
        confidence = min(0.99, 0.55 + document.quality_score * 0.4)
        return OcrTextResult(text=text, confidence=confidence, metadata={"model": settings.ocr_engine_name})

    async def extract_fields(self, text_result: OcrTextResult, document_type_code: str) -> Sequence[FieldResult]:
        _ = document_type_code
        parsed = self._parse_kv_text(text_result.text)
        fields: list[FieldResult] = []
        field_map = {
            "citizenship_number": parsed.get("citizenship_number") or parsed.get("citizenship no") or parsed.get("citizenship number"),
            "full_name": parsed.get("full_name") or parsed.get("name"),
            "date_of_birth": parsed.get("date_of_birth") or parsed.get("dob"),
            "issue_office": parsed.get("issue_office") or parsed.get("office"),
            "district": parsed.get("district"),
        }
        for field_name, value in field_map.items():
            confidence = 0.94 if value else 0.42
            fields.append(FieldResult(field_name=field_name, raw_value=value, normalized_value=self._normalize_value(field_name, value), confidence=confidence, validation_status="PASS" if value else "MISSING", source_language="en"))
        return fields

    async def validate(self, fields: Sequence[FieldResult], document_type_code: str) -> ValidationResult:
        _ = document_type_code
        issues: list[ValidationIssue] = []
        for field in fields:
            if field.validation_status == "MISSING":
                issues.append(ValidationIssue(code="OCR-5003", field_name=field.field_name, message=f"Missing required field: {field.field_name}", severity="medium"))
        status = "PASS" if not issues else "REVIEW"
        return ValidationResult(status=status, issues=issues)

    def _quality_score(self, content: bytes) -> float:
        if not content:
            return 0.0
        unique_ratio = len(set(content)) / len(content)
        return max(0.2, min(0.99, unique_ratio))

    def _parse_kv_text(self, text: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            values[key.strip().lower()] = value.strip()
        return values

    def _normalize_value(self, field_name: str, value: str | None) -> str | None:
        if value is None:
            return None
        if field_name == "citizenship_number":
            return value.replace(" ", "").upper()
        return value.strip()

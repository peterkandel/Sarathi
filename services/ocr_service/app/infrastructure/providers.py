from __future__ import annotations

from app.core.config import settings
from app.domain.ports import OcrProviderProtocol, OcrProviderRegistryProtocol
from app.infrastructure.engine import HeuristicOcrEngine


class OcrProviderRegistry(OcrProviderRegistryProtocol):
    def __init__(self) -> None:
        self._providers: dict[str, OcrProviderProtocol] = {
            "heuristic": HeuristicOcrEngine(),
        }

    def get_provider(self, provider_name: str) -> OcrProviderProtocol:
        try:
            return self._providers[provider_name]
        except KeyError as error:
            raise ValueError(f"Unsupported OCR provider: {provider_name}") from error


def get_default_ocr_provider() -> OcrProviderProtocol:
    registry = OcrProviderRegistry()
    return registry.get_provider(settings.ocr_provider_name)
from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.domain.ports import ObjectStorageProtocol


class FileSystemObjectStorage(ObjectStorageProtocol):
    def __init__(self, root_path: str | None = None) -> None:
        self.root_path = Path(root_path or settings.storage_root)
        self.root_path.mkdir(parents=True, exist_ok=True)

    async def save(self, storage_key: str, content: bytes, mime_type: str) -> None:
        _ = mime_type
        target_path = self.root_path / storage_key
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(content)

    async def load(self, storage_key: str) -> bytes:
        return (self.root_path / storage_key).read_bytes()

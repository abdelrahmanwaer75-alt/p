from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,254}$")


@dataclass(frozen=True)
class FileMetadata:
    path: str
    filename: str
    size: int
    mime_type: str | None
    extension: str
    modified_at: float
    is_directory: bool


class StorageService:
    """All media filesystem access goes through a single managed root."""

    def __init__(self, root: str | None = None) -> None:
        configured_root = root if root is not None else get_settings().download_directory
        self.root = Path(configured_root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_filename(self, filename: str) -> str:
        name = filename.strip()
        if not name or name in {".", ".."} or "/" in name or "\\" in name or not _SAFE_FILENAME.fullmatch(name):
            raise ValueError("Unsafe filename")
        return name

    def _managed(self, path: str | Path, *, allow_root: bool = False) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (self.root / candidate).resolve()
        if resolved == self.root and allow_root:
            return resolved
        if self.root not in resolved.parents:
            raise ValueError("Path escapes the Vidora media directory")
        return resolved

    def save(self, source: str | Path, filename: str, folder: str = "") -> FileMetadata:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError("Source file does not exist")
        safe_name = self._safe_filename(filename)
        destination_dir = self._managed(folder, allow_root=True)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = self._managed(destination_dir / safe_name)
        if destination == source_path:
            return self.metadata(destination)
        shutil.copy2(source_path, destination)
        return self.metadata(destination)

    def delete(self, path: str | Path) -> None:
        target = self._managed(path)
        if not target.exists():
            raise FileNotFoundError("File does not exist")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    def move(self, source: str | Path, destination: str | Path) -> FileMetadata:
        destination_path = self._managed(destination)
        source_path = self._managed(source)
        if not source_path.exists():
            raise FileNotFoundError("Source does not exist")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(destination_path)
        return self.metadata(destination_path)

    def rename(self, path: str | Path, new_filename: str) -> FileMetadata:
        source_path = self._managed(path)
        if not source_path.exists():
            raise FileNotFoundError("File does not exist")
        destination = source_path.with_name(self._safe_filename(new_filename))
        return self.move(source_path, destination)

    def exists(self, path: str | Path) -> bool:
        return self._managed(path).exists()

    def get_path(self, path: str | Path) -> Path:
        return self._managed(path)

    def metadata(self, path: str | Path) -> FileMetadata:
        target = self._managed(path)
        stat = target.stat()
        extension = target.suffix.lower().lstrip(".")
        mime_type = {"mp4": "video/mp4", "mkv": "video/x-matroska", "webm": "video/webm", "mp3": "audio/mpeg", "m4a": "audio/mp4"}.get(extension)
        return FileMetadata(path=str(target), filename=target.name, size=stat.st_size if target.is_file() else 0, mime_type=mime_type, extension=extension, modified_at=stat.st_mtime, is_directory=target.is_dir())

    def get_metadata(self, path: str | Path) -> FileMetadata:
        return self.metadata(path)

    def available_space(self) -> int:
        return shutil.disk_usage(self.root).free

    def relative_path(self, path: str | Path) -> str:
        return str(self._managed(path).relative_to(self.root))


class MediaStorage(StorageService):
    """Named media-storage boundary used by API and worker processes."""


__all__ = ["FileMetadata", "StorageService", "MediaStorage"]

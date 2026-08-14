from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.repositories.library import LibraryRepository
from app.schemas.files import FileActionResponse, FileInfoResponse, FileItem
from app.services.storage import FileMetadata, StorageService


class FileManagerService:
    def __init__(self, library: LibraryRepository | None = None, storage: StorageService | None = None) -> None:
        self.library = library or LibraryRepository()
        self.storage = storage or StorageService()

    def _item(self, library_item) -> FileItem:
        if not library_item.media_path:
            raise FileNotFoundError("Library item has no managed file")
        metadata = self.storage.metadata(library_item.media_path)
        return FileItem(
            library_id=library_item.id, path=self.storage.relative_path(metadata.path), media_path=self.storage.relative_path(metadata.path), filename=metadata.filename,
            size=metadata.size, mime_type=library_item.mime_type or metadata.mime_type, extension=metadata.extension,
            media_type=library_item.media_type, duration=library_item.duration, modified_at=datetime.fromtimestamp(metadata.modified_at, timezone.utc),
            is_favorite=library_item.is_favorite, title=library_item.title,
        )

    def list(self, owner_id: UUID, *, search: str | None = None, sort: str = "date", descending: bool = True) -> list[FileItem]:
        result: list[FileItem] = []
        for item in self.library.list(owner_id, files_only=True, search=search, sort=sort, descending=descending):
            try:
                result.append(self._item(item))
            except FileNotFoundError:
                # Never fabricate a file record when the durable file is absent.
                continue
        return result

    def info(self, owner_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        item = self.library.get(owner_id, item_id)
        return None if item is None else FileInfoResponse(file=self._item(item), available_space=self.storage.available_space())

    def rename(self, owner_id: UUID, item_id: UUID, filename: str) -> FileActionResponse | None:
        item = self.library.get(owner_id, item_id)
        if item is None:
            return None
        metadata = self.storage.rename(item.media_path or "", filename)
        updated = self.library.update_file(owner_id, item_id, media_path=metadata.path, filename=metadata.filename, file_size=metadata.size, mime_type=metadata.mime_type)
        return FileActionResponse(file=self._item(updated), message="File renamed") if updated else None

    def move(self, owner_id: UUID, item_id: UUID, folder: str) -> FileActionResponse | None:
        item = self.library.get(owner_id, item_id)
        if item is None:
            return None
        current = self.storage.metadata(item.media_path or "")
        destination = self.storage._managed(folder, allow_root=True) / current.filename
        metadata = self.storage.move(current.path, destination)
        updated = self.library.update_file(owner_id, item_id, media_path=metadata.path, filename=metadata.filename, file_size=metadata.size, mime_type=metadata.mime_type)
        return FileActionResponse(file=self._item(updated), message="File moved") if updated else None

    def delete(self, owner_id: UUID, item_id: UUID) -> FileActionResponse | None:
        item = self.library.get(owner_id, item_id)
        if item is None:
            return None
        verified = self._item(item)
        self.storage.delete(item.media_path or "")
        deleted = self.library.delete(owner_id, item_id)
        return FileActionResponse(file=verified, message="File deleted") if deleted else None

    def open(self, owner_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        return self.info(owner_id, item_id)

    def share(self, owner_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        # Sharing is a client action; this verifies the file and returns only managed metadata.
        return self.info(owner_id, item_id)

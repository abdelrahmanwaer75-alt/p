from uuid import UUID

from app.repositories.library import LibraryRepository
from app.services.files import FileManagerService
from app.services.storage import StorageService
from app.schemas.files import FileActionResponse, FileInfoResponse


class FileService:
    def __init__(self, repository: LibraryRepository, storage: StorageService | None = None) -> None:
        self.manager = FileManagerService(repository, storage=storage)

    def list(self, user_id: UUID, *, search: str | None, sort: str, descending: bool):
        return self.manager.list(user_id, search=search, sort=sort, descending=descending)

    def info(self, user_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        return self.manager.info(user_id, item_id)

    def rename(self, user_id: UUID, item_id: UUID, filename: str) -> FileActionResponse | None:
        return self.manager.rename(user_id, item_id, filename)

    def move(self, user_id: UUID, item_id: UUID, folder: str) -> FileActionResponse | None:
        return self.manager.move(user_id, item_id, folder)

    def delete(self, user_id: UUID, item_id: UUID) -> FileActionResponse | None:
        return self.manager.delete(user_id, item_id)

    def open(self, user_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        return self.manager.open(user_id, item_id)

    def share(self, user_id: UUID, item_id: UUID) -> FileInfoResponse | None:
        return self.manager.share(user_id, item_id)

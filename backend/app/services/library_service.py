from uuid import UUID

from app.repositories.library import LibraryRepository
from app.schemas.library import FavoriteUpdate, LibraryItem, LibraryItemCreate


class LibraryService:
    def __init__(self, repository: LibraryRepository) -> None:
        self.repository = repository

    def create(self, user_id: UUID, payload: LibraryItemCreate) -> LibraryItem:
        return self.repository.create(user_id, payload)

    def list(self, user_id: UUID, *, favorites_only: bool = False, history_only: bool = False) -> list[LibraryItem]:
        return self.repository.list(user_id, favorites_only=favorites_only, history_only=history_only)

    def set_favorite(self, user_id: UUID, item_id: UUID, payload: FavoriteUpdate) -> LibraryItem | None:
        return self.repository.set_favorite(user_id, item_id, payload.favorite)

    def mark_viewed(self, user_id: UUID, item_id: UUID) -> LibraryItem | None:
        return self.repository.mark_viewed(user_id, item_id)

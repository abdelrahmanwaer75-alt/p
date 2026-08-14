from __future__ import annotations

from uuid import UUID

from app.repositories.playlists import PlaylistRepository
from app.schemas.playlists import Playlist, PlaylistCreate, PlaylistItemCreate, PlaylistUpdate


class PlaylistService:
    def __init__(self, repository: PlaylistRepository) -> None:
        self.repository = repository

    def list(self, user_id: UUID) -> list[Playlist]:
        return self.repository.list(user_id)

    def get(self, user_id: UUID, playlist_id: UUID) -> Playlist | None:
        return self.repository.get(user_id, playlist_id)

    def create(self, user_id: UUID, payload: PlaylistCreate) -> Playlist:
        return self.repository.create(user_id, payload)

    def update(self, user_id: UUID, playlist_id: UUID, payload: PlaylistUpdate) -> Playlist | None:
        return self.repository.update(user_id, playlist_id, payload)

    def delete(self, user_id: UUID, playlist_id: UUID) -> Playlist | None:
        return self.repository.delete(user_id, playlist_id)

    def add_item(self, user_id: UUID, playlist_id: UUID, payload: PlaylistItemCreate) -> Playlist | None:
        return self.repository.add_item(user_id, playlist_id, payload)

    def remove_item(self, user_id: UUID, playlist_id: UUID, item_id: UUID) -> Playlist | None:
        return self.repository.remove_item(user_id, playlist_id, item_id)

    def reorder(self, user_id: UUID, playlist_id: UUID, item_ids: list[UUID]) -> Playlist | None:
        return self.repository.reorder(user_id, playlist_id, item_ids)

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlaylistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class PlaylistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class PlaylistItemCreate(BaseModel):
    library_item_id: UUID
    position: int | None = Field(default=None, ge=0)


class PlaylistReorder(BaseModel):
    item_ids: list[UUID] = Field(min_length=0, max_length=1000)


class PlaylistItem(BaseModel):
    id: UUID
    playlist_id: UUID
    library_item_id: UUID
    position: int
    title: str
    filename: str | None
    media_path: str | None
    media_type: str
    mime_type: str | None
    duration: int | None
    thumbnail: str | None
    created_at: datetime


class Playlist(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    items: list[PlaylistItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PlaylistMessage(BaseModel):
    message: str
    playlist: Playlist | None = None

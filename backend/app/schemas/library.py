from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class LibraryItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    media_path: str | None = Field(default=None, max_length=500)
    media_type: str = Field(default="video", max_length=40)
    filename: str | None = Field(default=None, max_length=500)
    mime_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = Field(default=None, ge=0)
    duration: int | None = Field(default=None, ge=0)
    thumbnail: str | None = Field(default=None, max_length=1000)


class LibraryItem(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    source_url: HttpUrl
    media_path: str | None
    media_type: str
    filename: str | None
    mime_type: str | None
    file_size: int | None
    duration: int | None
    thumbnail: str | None
    downloaded_at: datetime | None
    is_favorite: bool
    viewed_at: datetime | None
    created_at: datetime


class FavoriteUpdate(BaseModel):
    favorite: bool

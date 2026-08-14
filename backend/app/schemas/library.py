from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class LibraryItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    media_path: str | None = Field(default=None, max_length=500)
    media_type: str = Field(default="video", max_length=40)


class LibraryItem(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    source_url: HttpUrl
    media_path: str | None
    media_type: str
    is_favorite: bool
    viewed_at: datetime | None
    created_at: datetime


class FavoriteUpdate(BaseModel):
    favorite: bool

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class FileSort(StrEnum):
    NAME = "name"
    SIZE = "size"
    DATE = "date"
    TYPE = "type"


class FileItem(BaseModel):
    library_id: UUID
    path: str
    media_path: str
    filename: str
    size: int
    mime_type: str | None
    extension: str
    media_type: str
    duration: int | None
    modified_at: datetime | None
    is_favorite: bool
    title: str


class FileRenameRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)


class FileMoveRequest(BaseModel):
    folder: str = Field(default="", max_length=500)


class FileActionResponse(BaseModel):
    file: FileItem
    message: str


class FileInfoResponse(BaseModel):
    file: FileItem
    available_space: int

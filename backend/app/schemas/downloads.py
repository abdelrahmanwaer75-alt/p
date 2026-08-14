from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class DownloadStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadTaskCreate(BaseModel):
    source_url: HttpUrl
    format_id: str = Field(min_length=1, max_length=80)
    authorized: bool = Field(description="The client confirms it has authorization to download this source")


class DownloadTask(BaseModel):
    id: UUID
    owner_id: UUID | None = None
    source_url: HttpUrl
    format_id: str
    status: DownloadStatus
    progress_percent: float | None = Field(default=None, ge=0, le=100)
    progress_known: bool = False
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DownloadTaskAccepted(BaseModel):
    task: DownloadTask
    message: str

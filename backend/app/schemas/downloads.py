from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class DownloadStatus(StrEnum):
    QUEUED = "queued"
    STARTING = "starting"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadTaskCreate(BaseModel):
    source_url: HttpUrl
    platform: str = Field(default="generic", min_length=1, max_length=30)
    title: str | None = Field(default=None, max_length=500)
    format_id: str = Field(min_length=1, max_length=80)
    format_type: str | None = Field(default=None, max_length=20)
    extension: str | None = Field(default=None, max_length=20)
    mime_type: str | None = Field(default=None, max_length=120)
    quality: str | None = Field(default=None, max_length=80)
    authorized: bool = Field(description="The client confirms it has authorization to download this source")


class DownloadTask(BaseModel):
    id: UUID
    owner_id: UUID
    source_url: HttpUrl
    platform: str
    title: str | None = None
    format_id: str
    format_type: str | None = None
    extension: str | None = None
    mime_type: str | None = None
    quality: str | None = None
    status: DownloadStatus
    progress_percent: float | None = Field(default=None, ge=0, le=100)
    bytes_downloaded: int = Field(default=0, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    speed: float | None = Field(default=None, ge=0)
    eta: int | None = Field(default=None, ge=0)
    progress_known: bool = False
    output_path: str | None = None
    output_filename: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    updated_at: datetime
    retry_count: int = Field(default=0, ge=0)


class DownloadTaskAccepted(BaseModel):
    task: DownloadTask
    message: str


class DownloadCancelResponse(BaseModel):
    task: DownloadTask
    message: str

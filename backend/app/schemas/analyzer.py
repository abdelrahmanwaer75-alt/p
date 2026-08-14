from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Platform(StrEnum):
    REDDIT = "reddit"
    VIMEO = "vimeo"
    DAILYMOTION = "dailymotion"
    SOUNDCLOUD = "soundcloud"
    TWITCH = "twitch"
    GENERIC = "generic"


class MediaKind(StrEnum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    UNKNOWN = "unknown"


class MediaFormat(BaseModel):
    format_id: str
    extension: str
    kind: MediaKind
    resolution: Optional[str] = None
    quality: Optional[str] = None
    mime_type: Optional[str] = None
    estimated_size_bytes: Optional[int] = Field(default=None, ge=0)
    bitrate: Optional[int] = Field(default=None, ge=0)
    fps: Optional[float] = Field(default=None, ge=0)


class AnalyzerResult(BaseModel):
    url: HttpUrl
    platform: Platform
    supported: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[HttpUrl] = None
    duration: Optional[int] = Field(default=None, ge=0)
    uploader: Optional[str] = None
    formats: list[MediaFormat] = Field(default_factory=list)
    audio_formats: list[MediaFormat] = Field(default_factory=list)
    video_formats: list[MediaFormat] = Field(default_factory=list)
    estimated_size: Optional[int] = Field(default=None, ge=0)
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    quality: Optional[str] = None
    bitrate: Optional[int] = Field(default=None, ge=0)
    resolution: Optional[str] = None
    fps: Optional[float] = Field(default=None, ge=0)
    restrictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    message: str

    # Backward-compatible fields retained for existing Flutter/API consumers.
    content_kind: MediaKind = MediaKind.UNKNOWN
    creator: Optional[str] = None
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    thumbnail_url: Optional[HttpUrl] = None

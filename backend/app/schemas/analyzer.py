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
    estimated_size_bytes: Optional[int] = Field(default=None, ge=0)


class AnalyzerResult(BaseModel):
    url: HttpUrl
    platform: Platform
    content_kind: MediaKind
    title: Optional[str] = None
    description: Optional[str] = None
    creator: Optional[str] = None
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    thumbnail_url: Optional[HttpUrl] = None
    formats: list[MediaFormat] = Field(default_factory=list)
    supported: bool = False
    message: str

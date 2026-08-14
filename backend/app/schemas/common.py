from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    timestamp: datetime


class VersionResponse(BaseModel):
    name: str
    version: str
    api_prefix: str


class AnalyzeRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def require_http_scheme(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme not in {"http", "https"}:
            raise ValueError("Only HTTP and HTTPS URLs are supported")
        return value


class AnalyzeResponse(BaseModel):
    status: Literal["accepted"]
    message: str = Field(description="Human-readable next-step message")
    url: HttpUrl


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

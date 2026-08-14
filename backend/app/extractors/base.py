from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Awaitable, Callable

from app.schemas.analyzer import AnalyzerResult, MediaFormat, MediaKind, Platform
from app.schemas.downloads import DownloadTask


class ExtractorUnavailable(RuntimeError):
    """Raised when no approved adapter is configured for a supported platform."""


class AuthorizationRequired(PermissionError):
    """Raised when an adapter requires explicit user authorization."""


class DownloadNotAvailable(RuntimeError):
    """Raised when an approved extractor has no implemented download operation."""


class TransientDownloadError(RuntimeError):
    """Raised for failures that may succeed when retried with bounded backoff."""


@dataclass(frozen=True)
class DownloadResult:
    output_path: str
    output_filename: str
    bytes_downloaded: int
    total_bytes: int | None
    extension: str | None
    mime_type: str | None


@dataclass(frozen=True)
class ExtractorMetadata:
    title: str | None = None
    description: str | None = None
    thumbnail: str | None = None
    duration: int | None = None
    uploader: str | None = None
    mime_type: str | None = None
    extension: str | None = None
    quality: str | None = None
    bitrate: int | None = None
    resolution: str | None = None
    fps: float | None = None
    estimated_size: int | None = None
    limitations: tuple[str, ...] = ()


class PlatformExtractor(ABC):
    platform: Platform
    available: bool = False

    async def analyze(self, url: str, authorized: bool = False) -> AnalyzerResult:
        if not self.available:
            return self.unavailable_result(url)
        self.validate_authorization(authorized)
        try:
            metadata = await self.get_metadata(url)
            formats = await self.get_formats(url)
        except ExtractorUnavailable:
            return self.unavailable_result(url)
        return self.build_result(url, metadata, formats)

    def validate_authorization(self, authorized: bool) -> None:
        if not authorized:
            raise AuthorizationRequired("Explicit user authorization is required before platform analysis")

    @abstractmethod
    async def get_metadata(self, url: str) -> ExtractorMetadata:
        """Return verified metadata from an approved platform adapter."""

    @abstractmethod
    async def get_formats(self, url: str) -> list[MediaFormat]:
        """Return verified formats from an approved platform adapter."""

    async def download(
        self,
        task: DownloadTask,
        progress_callback: Callable[[int, int | None, float | None, int | None], Awaitable[None]],
        cancellation_requested: Callable[[], Awaitable[bool]],
    ) -> DownloadResult:
        raise DownloadNotAvailable("No authorized download implementation is configured")

    def unavailable_result(self, url: str) -> AnalyzerResult:
        return AnalyzerResult(
            url=url,
            platform=self.platform,
            supported=False,
            content_kind=MediaKind.UNKNOWN,
            formats=[],
            audio_formats=[],
            video_formats=[],
            restrictions=["adapter_unavailable"],
            limitations=("metadata_unavailable", "formats_unavailable", "download_unavailable"),
            message=(
                "FEATURE_NOT_AVAILABLE: "
                f"{self.platform.value.title()} is recognized, but no platform-approved extractor is configured yet. "
                "No metadata, formats, size, duration, progress, or download URL were fetched or fabricated."
            ),
        )

    def build_result(self, url: str, metadata: ExtractorMetadata, formats: list[MediaFormat]) -> AnalyzerResult:
        audio_formats = [item for item in formats if item.kind == MediaKind.AUDIO]
        video_formats = [item for item in formats if item.kind == MediaKind.VIDEO]
        content_kind = MediaKind.VIDEO if video_formats else MediaKind.AUDIO if audio_formats else MediaKind.UNKNOWN
        return AnalyzerResult(
            url=url,
            platform=self.platform,
            supported=True,
            title=metadata.title,
            description=metadata.description,
            thumbnail=metadata.thumbnail,
            duration=metadata.duration,
            uploader=metadata.uploader,
            formats=formats,
            audio_formats=audio_formats,
            video_formats=video_formats,
            estimated_size=metadata.estimated_size,
            mime_type=metadata.mime_type,
            extension=metadata.extension,
            quality=metadata.quality,
            bitrate=metadata.bitrate,
            resolution=metadata.resolution,
            fps=metadata.fps,
            limitations=list(metadata.limitations),
            content_kind=content_kind,
            creator=metadata.uploader,
            duration_seconds=metadata.duration,
            thumbnail_url=metadata.thumbnail,
            message="Metadata and formats were returned by an authorized platform extractor.",
        )

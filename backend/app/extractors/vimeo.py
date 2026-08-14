from app.extractors.base import ExtractorMetadata, ExtractorUnavailable, PlatformExtractor
from app.schemas.analyzer import MediaFormat, Platform


class VimeoExtractor(PlatformExtractor):
    platform = Platform.VIMEO

    async def get_metadata(self, url: str) -> ExtractorMetadata:
        raise ExtractorUnavailable("Vimeo adapter is not configured")

    async def get_formats(self, url: str) -> list[MediaFormat]:
        raise ExtractorUnavailable("Vimeo adapter is not configured")

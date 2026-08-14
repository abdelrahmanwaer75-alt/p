from app.extractors.base import ExtractorMetadata, ExtractorUnavailable, PlatformExtractor
from app.schemas.analyzer import MediaFormat, Platform


class RedditExtractor(PlatformExtractor):
    platform = Platform.REDDIT

    async def get_metadata(self, url: str) -> ExtractorMetadata:
        raise ExtractorUnavailable("Reddit adapter is not configured")

    async def get_formats(self, url: str) -> list[MediaFormat]:
        raise ExtractorUnavailable("Reddit adapter is not configured")

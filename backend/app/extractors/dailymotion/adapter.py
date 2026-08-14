from app.extractors.base import ExtractorMetadata, ExtractorUnavailable, PlatformExtractor
from app.schemas.analyzer import MediaFormat, Platform


class DailymotionExtractor(PlatformExtractor):
    platform = Platform.DAILYMOTION

    async def get_metadata(self, url: str) -> ExtractorMetadata:
        raise ExtractorUnavailable("Dailymotion adapter is not configured")

    async def get_formats(self, url: str) -> list[MediaFormat]:
        raise ExtractorUnavailable("Dailymotion adapter is not configured")

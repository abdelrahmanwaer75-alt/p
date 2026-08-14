from app.extractors.base import ExtractorMetadata, ExtractorUnavailable, PlatformExtractor
from app.schemas.analyzer import MediaFormat, Platform


class TwitchExtractor(PlatformExtractor):
    platform = Platform.TWITCH

    async def get_metadata(self, url: str) -> ExtractorMetadata:
        raise ExtractorUnavailable("Twitch adapter is not configured")

    async def get_formats(self, url: str) -> list[MediaFormat]:
        raise ExtractorUnavailable("Twitch adapter is not configured")

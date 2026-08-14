from app.extractors.base import ExtractorMetadata, ExtractorUnavailable, PlatformExtractor
from app.schemas.analyzer import MediaFormat, Platform


class SoundCloudExtractor(PlatformExtractor):
    platform = Platform.SOUNDCLOUD

    async def get_metadata(self, url: str) -> ExtractorMetadata:
        raise ExtractorUnavailable("SoundCloud adapter is not configured")

    async def get_formats(self, url: str) -> list[MediaFormat]:
        raise ExtractorUnavailable("SoundCloud adapter is not configured")

from dataclasses import dataclass

from app.extractors.base import PlatformExtractor
from app.extractors.dailymotion import DailymotionExtractor
from app.extractors.reddit import RedditExtractor
from app.extractors.soundcloud import SoundCloudExtractor
from app.extractors.twitch import TwitchExtractor
from app.extractors.vimeo import VimeoExtractor
from app.schemas.analyzer import Platform


SUPPORTED_PLATFORMS = (
    Platform.REDDIT,
    Platform.VIMEO,
    Platform.DAILYMOTION,
    Platform.SOUNDCLOUD,
    Platform.TWITCH,
)
ALLOWED_PLATFORMS = frozenset(SUPPORTED_PLATFORMS)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def authorize_analysis(*, authorized: bool) -> PolicyDecision:
    if not authorized:
        return PolicyDecision(False, "Explicit user authorization is required before source analysis")
    return PolicyDecision(True, "Authorized analysis may proceed through a platform-approved adapter")


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors: dict[Platform, PlatformExtractor] = {
            Platform.REDDIT: RedditExtractor(),
            Platform.VIMEO: VimeoExtractor(),
            Platform.DAILYMOTION: DailymotionExtractor(),
            Platform.SOUNDCLOUD: SoundCloudExtractor(),
            Platform.TWITCH: TwitchExtractor(),
        }

    def get(self, platform: Platform) -> PlatformExtractor | None:
        return self._extractors.get(platform)

    def is_allowed(self, platform: Platform) -> bool:
        return platform in ALLOWED_PLATFORMS

    def supported_platforms(self) -> list[Platform]:
        return [platform for platform in SUPPORTED_PLATFORMS if self._extractors[platform].available]

    def allowed_platforms(self) -> frozenset[Platform]:
        return ALLOWED_PLATFORMS


registry = ExtractorRegistry()

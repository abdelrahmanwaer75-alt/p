from dataclasses import dataclass
from typing import Protocol

from app.schemas.analyzer import AnalyzerResult, Platform


class PlatformExtractor(Protocol):
    platform: Platform

    async def analyze(self, url: str, authorized: bool) -> AnalyzerResult: ...


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def authorize_analysis(*, authorized: bool) -> PolicyDecision:
    if not authorized:
        return PolicyDecision(False, "Explicit user authorization is required before source analysis")
    return PolicyDecision(True, "Authorized analysis may proceed through a platform-approved adapter")


class UnconfiguredExtractor:
    def __init__(self, platform: Platform) -> None:
        self.platform = platform

    async def analyze(self, url: str, authorized: bool) -> AnalyzerResult:
        decision = authorize_analysis(authorized=authorized)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        raise NotImplementedError(f"No platform-approved extractor configured for {self.platform.value}")


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors = {platform: UnconfiguredExtractor(platform) for platform in Platform}

    def get(self, platform: Platform) -> PlatformExtractor:
        return self._extractors[platform]

    def supported_platforms(self) -> list[Platform]:
        return [platform for platform, extractor in self._extractors.items() if not isinstance(extractor, UnconfiguredExtractor)]


registry = ExtractorRegistry()

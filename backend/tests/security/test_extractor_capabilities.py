import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.extractors.base import DownloadNotAvailable
from app.extractors.registry import SUPPORTED_PLATFORMS, registry
from app.schemas.analyzer import Platform
from app.schemas.downloads import DownloadStatus, DownloadTask


@pytest.mark.parametrize("platform", SUPPORTED_PLATFORMS)
def test_allowlisted_platform_is_explicitly_disabled_until_approved_adapter_exists(platform: Platform) -> None:
    extractor = registry.get(platform)
    assert extractor is not None
    assert extractor.platform is platform
    assert extractor.available is False

    result = asyncio.run(extractor.analyze(f"https://example.invalid/{platform.value}"))
    assert result.supported is False
    assert result.formats == []
    assert result.audio_formats == []
    assert result.video_formats == []
    assert result.title is None
    assert result.duration is None
    assert result.estimated_size is None
    assert "FEATURE_NOT_AVAILABLE" in result.message


@pytest.mark.parametrize("platform", SUPPORTED_PLATFORMS)
def test_disabled_platform_download_never_creates_output(platform: Platform) -> None:
    extractor = registry.get(platform)
    assert extractor is not None
    task = DownloadTask(
        id=uuid4(),
        owner_id=uuid4(),
        source_url=f"https://example.invalid/{platform.value}",
        platform=platform.value,
        title=None,
        format_id="unknown",
        format_type="unknown",
        extension=None,
        mime_type=None,
        quality=None,
        status=DownloadStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async def progress(*_: object) -> None:
        raise AssertionError("disabled adapters must not report fabricated progress")

    async def cancellation_requested() -> bool:
        return False

    with pytest.raises(DownloadNotAvailable):
        asyncio.run(extractor.download(task, progress, cancellation_requested))

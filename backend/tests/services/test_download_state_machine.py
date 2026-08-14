from typing import cast
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.core.typing import as_http_url
from app.queue.stream import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus, DownloadTaskCreate
from app.services.download_state_machine import can_transition, require_transition
from app.services.downloads import DownloadService


OWNER = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class QueueFake:
    def enqueue(self, *_args, **_kwargs):
        return "1-0"

    def publish_event(self, *_args, **_kwargs):
        return True


class ExtractorFake:
    available = True


class RegistryFake:
    def get(self, _platform):
        return ExtractorFake()


def payload() -> DownloadTaskCreate:
    return DownloadTaskCreate(source_url=as_http_url("https://vimeo.com/123"), platform="vimeo", format_id="mp4", authorized=True)


def test_download_state_machine_allows_only_declared_lifecycle_edges() -> None:
    assert can_transition(DownloadStatus.QUEUED, DownloadStatus.STARTING)
    assert can_transition(DownloadStatus.STARTING, DownloadStatus.DOWNLOADING)
    assert can_transition(DownloadStatus.DOWNLOADING, DownloadStatus.COMPLETED)
    assert can_transition(DownloadStatus.DOWNLOADING, DownloadStatus.CANCELLING)
    assert can_transition(DownloadStatus.CANCELLING, DownloadStatus.CANCELLED)
    assert not can_transition(DownloadStatus.COMPLETED, DownloadStatus.DOWNLOADING)
    with pytest.raises(ValueError):
        require_transition(DownloadStatus.CANCELLED, DownloadStatus.STARTING)


def test_pause_and_resume_are_explicitly_unavailable_without_native_adapter_support() -> None:
    service = DownloadService(DownloadRepository(), queue=cast(DownloadQueue, QueueFake()), extractor_registry=RegistryFake())
    task = service.create(payload(), OWNER)
    with pytest.raises(HTTPException) as pause_error:
        service.pause(task.id, OWNER)
    assert pause_error.value.status_code == 501
    with pytest.raises(HTTPException) as resume_error:
        service.resume(task.id, OWNER)
    assert resume_error.value.status_code == 501

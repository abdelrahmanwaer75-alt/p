import asyncio
from typing import cast
from uuid import UUID

from app.core.typing import as_http_url
from app.queue.stream import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus, DownloadTaskCreate
from worker import process_once


class FakeQueue:
    def __init__(self, task_id):
        self.task_id = task_id

    def dequeue(self, timeout=1):
        task_id, self.task_id = self.task_id, None
        return task_id


def test_worker_marks_task_failed_without_authorized_adapter() -> None:
    repository = DownloadRepository()
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    task = repository.create(
        DownloadTaskCreate(source_url=as_http_url("https://example.com/a.mp4"), format_id="mp4", authorized=True),
        owner_id,
    )
    asyncio.run(process_once(cast(DownloadQueue, FakeQueue(task.id)), repository))
    current = repository.get_any(task.id)
    assert current is not None
    assert current.status == DownloadStatus.FAILED

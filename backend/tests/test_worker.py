import asyncio
from uuid import UUID

from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus, DownloadTaskCreate
from worker import process_once


class FakeQueue:
    def __init__(self, task_id):
        self.task_id = task_id

    def dequeue(self, timeout=1):
        task_id, self.task_id = self.task_id, None
        return task_id


def test_worker_marks_task_failed_without_authorized_adapter(tmp_path) -> None:
    repository = DownloadRepository(str(tmp_path / "worker.db"))
    owner_id = UUID("11111111-1111-1111-1111-111111111111")
    task = repository.create(
        DownloadTaskCreate(source_url="https://example.com/a.mp4", format_id="mp4", authorized=True),
        owner_id,
    )
    asyncio.run(process_once(FakeQueue(task.id), repository))
    assert repository.get_any(task.id).status == DownloadStatus.FAILED

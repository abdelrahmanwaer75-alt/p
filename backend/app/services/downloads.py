from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.schemas.downloads import DownloadStatus, DownloadTask, DownloadTaskCreate


class AuthorizedDownloadWorker:
    """Boundary for a future policy-aware media worker.

    This class intentionally does not invoke yt-dlp, FFmpeg, subprocesses, or
    arbitrary shell commands. A later implementation must receive a validated
    extractor plan and enforce authorization and platform policy first.
    """

    async def execute(self, task: DownloadTask) -> DownloadTask:
        raise NotImplementedError("No authorized download adapter is configured")


class DownloadService:
    def __init__(self) -> None:
        self._tasks: dict[UUID, DownloadTask] = {}
        self._worker = AuthorizedDownloadWorker()

    def create(self, payload: DownloadTaskCreate) -> DownloadTask:
        if not payload.authorized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User authorization is required")
        now = datetime.now(timezone.utc)
        task = DownloadTask(
            id=uuid4(),
            source_url=payload.source_url,
            format_id=payload.format_id,
            status=DownloadStatus.QUEUED,
            progress_percent=None,
            progress_known=False,
            created_at=now,
            updated_at=now,
        )
        self._tasks[task.id] = task
        return task

    def get(self, task_id: UUID) -> DownloadTask:
        task = self._tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")
        return task

    def list(self) -> list[DownloadTask]:
        return list(self._tasks.values())

    async def run(self, task_id: UUID) -> DownloadTask:
        task = self.get(task_id)
        try:
            return await self._worker.execute(task)
        except NotImplementedError as exc:
            failed = task.model_copy(update={
                "status": DownloadStatus.FAILED,
                "error_message": str(exc),
                "updated_at": datetime.now(timezone.utc),
            })
            self._tasks[task.id] = failed
            return failed


_download_service = DownloadService()


def get_download_service() -> DownloadService:
    return _download_service

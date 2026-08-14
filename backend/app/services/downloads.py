from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus, DownloadTask, DownloadTaskCreate


class AuthorizedDownloadWorker:
    """Boundary for a future policy-aware media worker."""

    async def execute(self, task: DownloadTask) -> DownloadTask:
        raise NotImplementedError("No authorized download adapter is configured")


class DownloadService:
    def __init__(self, repository: DownloadRepository) -> None:
        self._repository = repository
        self._worker = AuthorizedDownloadWorker()

    def create(self, payload: DownloadTaskCreate, owner_id: UUID) -> DownloadTask:
        if not payload.authorized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User authorization is required")
        return self._repository.create(payload, owner_id)

    def get(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self._repository.get(task_id, owner_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")
        return task

    def list(self, owner_id: UUID) -> list[DownloadTask]:
        return self._repository.list(owner_id)

    async def run(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        try:
            return await self._worker.execute(task)
        except NotImplementedError as exc:
            failed = task.model_copy(update={
                "status": DownloadStatus.FAILED,
                "error_message": str(exc),
                "updated_at": datetime.now(timezone.utc),
            })
            return self._repository.save(failed)


_download_service = DownloadService(DownloadRepository(get_settings().download_db_path))


def get_download_service() -> DownloadService:
    return _download_service

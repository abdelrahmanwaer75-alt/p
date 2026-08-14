from uuid import UUID

from fastapi import HTTPException, status

from app.extractors.registry import registry
from app.queue import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus, DownloadTask, DownloadTaskCreate


class DownloadService:
    def __init__(self, repository: DownloadRepository, queue: DownloadQueue | None = None, extractor_registry=registry) -> None:
        self._repository = repository
        self._queue = queue or DownloadQueue()
        self._extractors = extractor_registry

    def create(self, payload: DownloadTaskCreate, owner_id: UUID, *, idempotency_key: str | None = None) -> DownloadTask:
        if not payload.authorized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User authorization is required")
        extractor = self._extractors.get(payload.platform)
        if extractor is None or not extractor.available:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="FEATURE_NOT_AVAILABLE")
        existing = self._repository.get_by_idempotency(idempotency_key, owner_id) if idempotency_key else None
        if existing:
            return existing
        try:
            task = self._repository.create_with_idempotency(payload, owner_id, idempotency_key)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unable to persist download task") from exc
        if task.status != DownloadStatus.QUEUED:
            return task
        message_id = self._queue.enqueue(task.id, attempt=task.retry_count)
        if message_id is None:
            self._repository.update(
                task.id,
                status=DownloadStatus.FAILED.value,
                error_code="REDIS_UNAVAILABLE",
                error_message="Redis Streams unavailable; download was not queued",
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis Streams unavailable; download was not queued")
        self._queue.publish_event(task.id, "queued", message_id=message_id)
        return task

    def get(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self._repository.get(task_id, owner_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")
        return task

    def list(self, owner_id: UUID) -> list[DownloadTask]:
        return self._repository.list(owner_id)

    def requeue(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        if task.status in {DownloadStatus.COMPLETED, DownloadStatus.CANCELLED}:
            return task
        updated = self._repository.update(task.id, status=DownloadStatus.QUEUED.value, error_code=None, error_message=None)
        if updated is None:
            raise HTTPException(status_code=404, detail="Download task not found")
        if self._queue.enqueue(task.id, attempt=updated.retry_count) is None:
            self._repository.update(task.id, status=DownloadStatus.FAILED.value, error_code="REDIS_UNAVAILABLE", error_message="Redis Streams unavailable; download was not queued")
            raise HTTPException(status_code=503, detail="Redis Streams unavailable; download was not queued")
        return updated

    def pause(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        self.get(task_id, owner_id)
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="FEATURE_NOT_AVAILABLE: pause requires an extractor with native pause support")

    def resume(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        self.get(task_id, owner_id)
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="FEATURE_NOT_AVAILABLE: resume requires an extractor with native pause support")

    def retry(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        if task.status != DownloadStatus.FAILED:
            raise HTTPException(status_code=409, detail="Only failed downloads can be retried")
        if task.retry_count >= 3:
            raise HTTPException(status_code=409, detail="Download retry limit has been reached")
        updated = self._repository.update(task.id, status=DownloadStatus.QUEUED.value, error_code=None, error_message=None)
        if updated is None or self._queue.enqueue(task.id, attempt=updated.retry_count) is None:
            self._repository.update(task.id, status=DownloadStatus.FAILED.value, error_code="REDIS_UNAVAILABLE", error_message="Redis Streams unavailable; download was not retried")
            raise HTTPException(status_code=503, detail="Redis Streams unavailable; download was not retried")
        return updated

    def open(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        if task.status != DownloadStatus.COMPLETED or not task.output_path:
            raise HTTPException(status_code=409, detail="Only completed downloads can be opened")
        return task

    def delete(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        if task.status not in {DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED}:
            raise HTTPException(status_code=409, detail="Active downloads cannot be deleted")
        deleted = self._repository.delete(task_id, owner_id)
        if deleted is None:
            raise HTTPException(status_code=404, detail="Download task not found")
        return deleted

    def cancel(self, task_id: UUID, owner_id: UUID) -> DownloadTask:
        task = self.get(task_id, owner_id)
        if task.status == DownloadStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed downloads cannot be cancelled")
        updated = self._repository.request_cancel(task_id, owner_id)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download task not found")
        if updated.status == DownloadStatus.CANCELLING:
            self._queue.publish_event(task_id, "cancelling")
        elif updated.status == DownloadStatus.CANCELLED:
            self._queue.publish_event(task_id, "cancelled")
        return updated


_download_service = DownloadService(DownloadRepository())


def get_download_service() -> DownloadService:
    return _download_service

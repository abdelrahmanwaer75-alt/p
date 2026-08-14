from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID
from pathlib import Path

from sqlalchemy import text
from app.db import engine

from app.core.config import get_settings
from app.db import init_database
from app.extractors.base import AuthorizationRequired, DownloadNotAvailable, ExtractorUnavailable, TransientDownloadError
from app.extractors.registry import registry
from app.repositories.downloads import DownloadRepository
from app.repositories.library import LibraryRepository
from app.queue import DownloadQueue, QueueMessage, QueueUnavailable
from app.services.download_retry import DownloadRetryPolicy
from app.schemas.downloads import DownloadStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vidora.worker")
RETRY_POLICY = DownloadRetryPolicy(max_retries=3)
MAX_RETRIES = RETRY_POLICY.max_retries


def now() -> datetime:
    return datetime.now(timezone.utc)


def _ack(queue: DownloadQueue, message_id: str) -> None:
    ack = getattr(queue, "ack", None)
    if ack is not None:
        ack(message_id)


def _publish(queue: DownloadQueue, task_id: UUID, event: str, **payload: object) -> None:
    publish = getattr(queue, "publish_event", None)
    if publish is not None:
        publish(task_id, event, **payload)


def _dead_letter(queue: DownloadQueue, message: QueueMessage, *, reason: str, attempt: int) -> None:
    dead_letter = getattr(queue, "dead_letter", None)
    if dead_letter is not None:
        dead_letter(message, reason=reason, attempt=attempt)


def _error_task(repository: DownloadRepository, task_id: UUID, code: str, message: str):
    return repository.update(
        task_id,
        status=DownloadStatus.FAILED.value,
        error_code=code,
        error_message=message,
        progress_known=False,
    )


async def _next_message(queue: DownloadQueue, timeout: int) -> QueueMessage | None:
    recover = getattr(queue, "recover_pending", None)
    if recover is not None:
        recovered = recover(min_idle_ms=60_000, count=1)
        if recovered:
            return recovered[0]
    return queue.dequeue(timeout=timeout)


async def process_once(
    queue: DownloadQueue,
    repository: DownloadRepository,
    *,
    library_repository: LibraryRepository | None = None,
    extractor_registry=registry,
    sleep: Callable[[float], object] | None = None,
) -> bool:
    message = await _next_message(queue, timeout=1)
    if message is None:
        return False
    # Compatibility with simple test queues from the previous phase.
    if isinstance(message, UUID):
        message = QueueMessage(message_id="legacy", task_id=message, attempt=0)
    task = repository.get_any(message.task_id)
    if task is None:
        _ack(queue, message.message_id)
        return True

    if task.status in {DownloadStatus.COMPLETED, DownloadStatus.CANCELLED, DownloadStatus.FAILED}:
        _ack(queue, message.message_id)
        return True
    if task.status == DownloadStatus.CANCELLING:
        cancelled = repository.update(task.id, status=DownloadStatus.CANCELLED.value, cancelled_at=now(), error_code=None, error_message=None)
        _ack(queue, message.message_id)
        _publish(queue, task.id, "cancelled")
        return cancelled is not None

    repository.update(task.id, status=DownloadStatus.STARTING.value, started_at=task.started_at or now(), error_code=None, error_message=None)
    _publish(queue, task.id, "starting")
    task = repository.get_any(task.id)
    if task is None:
        _ack(queue, message.message_id)
        return True

    extractor = extractor_registry.get(task.platform)
    if extractor is None or not extractor.available:
        _error_task(repository, task.id, "FEATURE_NOT_AVAILABLE", "FEATURE_NOT_AVAILABLE: no authorized extractor is implemented for this platform")
        _ack(queue, message.message_id)
        _publish(queue, task.id, "failed", error_code="FEATURE_NOT_AVAILABLE")
        return True

    async def is_cancelled() -> bool:
        current = repository.get_any(task.id)
        return current is None or current.status in {DownloadStatus.CANCELLING, DownloadStatus.CANCELLED}

    async def progress(bytes_downloaded: int, total_bytes: int | None, speed: float | None, eta: int | None) -> None:
        current = repository.get_any(task.id)
        if current is None or current.status in {DownloadStatus.CANCELLING, DownloadStatus.CANCELLED}:
            return
        percent = (bytes_downloaded / total_bytes * 100) if total_bytes else None
        repository.update(
            task.id,
            status=DownloadStatus.DOWNLOADING.value,
            progress_percent=percent,
            progress_known=total_bytes is not None,
            bytes_downloaded=bytes_downloaded,
            total_bytes=total_bytes,
            speed=speed,
            eta=eta,
        )
        progress_payload: dict[str, object] = {"bytes_downloaded": bytes_downloaded}
        if total_bytes is not None:
            progress_payload.update({"progress_percent": percent, "total_bytes": total_bytes})
        _publish(queue, task.id, "progress", **progress_payload)

    try:
        repository.update(task.id, status=DownloadStatus.DOWNLOADING.value)
        result = await extractor.download(task, progress, is_cancelled)
        current = repository.get_any(task.id)
        if current is None:
            _ack(queue, message.message_id)
            return True
        if current.status in {DownloadStatus.CANCELLING, DownloadStatus.CANCELLED} or await is_cancelled():
            repository.update(task.id, status=DownloadStatus.CANCELLED.value, cancelled_at=now())
            _ack(queue, message.message_id)
            _publish(queue, task.id, "cancelled")
            return True
        completed = repository.update(
            task.id,
            status=DownloadStatus.COMPLETED.value,
            progress_percent=100,
            progress_known=True,
            bytes_downloaded=result.bytes_downloaded,
            total_bytes=result.total_bytes,
            output_path=result.output_path,
            output_filename=result.output_filename,
            extension=result.extension,
            mime_type=result.mime_type,
            completed_at=now(),
            error_code=None,
            error_message=None,
        )
        if completed and library_repository is not None:
            from app.schemas.library import LibraryItemCreate
            library_repository.create(
                completed.owner_id,
                LibraryItemCreate(
                    title=completed.title or completed.output_filename or "download",
                    source_url=completed.source_url,
                    media_path=completed.output_path,
                    media_type=completed.format_type or "video",
                    filename=completed.output_filename,
                    mime_type=result.mime_type,
                    file_size=result.bytes_downloaded,
                    duration=None,
                    thumbnail=None,
                ),
            )
        _ack(queue, message.message_id)
        _publish(queue, task.id, "completed", output_path=result.output_path)
        return True
    except (DownloadNotAvailable, ExtractorUnavailable, AuthorizationRequired) as exc:
        _error_task(repository, task.id, "FEATURE_NOT_AVAILABLE", f"FEATURE_NOT_AVAILABLE: {exc}")
        _ack(queue, message.message_id)
        _publish(queue, task.id, "failed", error_code="FEATURE_NOT_AVAILABLE")
        return True
    except TransientDownloadError as exc:
        current = repository.get_any(task.id)
        if current is not None and current.status in {DownloadStatus.CANCELLING, DownloadStatus.CANCELLED}:
            repository.update(task.id, status=DownloadStatus.CANCELLED.value, cancelled_at=now(), error_code=None, error_message=None)
            _ack(queue, message.message_id)
            _publish(queue, task.id, "cancelled")
            return True
        next_retry = RETRY_POLICY.next_attempt(task.retry_count)
        if RETRY_POLICY.should_retry(task.retry_count):
            repository.update(task.id, status=DownloadStatus.QUEUED.value, retry_count=next_retry, error_code="TRANSIENT_RETRY", error_message=str(exc))
            delay = RETRY_POLICY.delay(next_retry)
            if sleep is not None:
                result = sleep(delay)
                if asyncio.iscoroutine(result):
                    await result
            queued = queue.retry(message, delay_seconds=delay, attempt=next_retry)
            if queued is None:
                _error_task(repository, task.id, "REDIS_UNAVAILABLE", "Redis Streams unavailable while scheduling retry")
                return True
            _ack(queue, message.message_id)
            _publish(queue, task.id, "queued", retry_count=next_retry)
            return True
        _error_task(repository, task.id, "RETRY_EXHAUSTED", str(exc))
        _dead_letter(queue, message, reason=str(exc), attempt=next_retry)
        _publish(queue, task.id, "failed", error_code="RETRY_EXHAUSTED")
        return True
    except Exception as exc:
        current = repository.get_any(task.id)
        if current is not None and current.status in {DownloadStatus.CANCELLING, DownloadStatus.CANCELLED}:
            repository.update(task.id, status=DownloadStatus.CANCELLED.value, cancelled_at=now(), error_code=None, error_message=None)
            _ack(queue, message.message_id)
            _publish(queue, task.id, "cancelled")
            return True
        logger.exception("Permanent download failure for task %s", task.id)
        _error_task(repository, task.id, "DOWNLOAD_FAILED", str(exc))
        _ack(queue, message.message_id)
        _publish(queue, task.id, "failed", error_code="DOWNLOAD_FAILED")
        return True


def _worker_ready_file() -> Path:
    return Path(os.getenv("WORKER_READY_FILE", "/tmp/vidora-worker.ready"))


def _set_worker_ready(ready: bool) -> None:
    marker = _worker_ready_file()
    if ready:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    elif marker.exists():
        marker.unlink()


def _dependencies_ready(queue: DownloadQueue) -> bool:
    if not queue.ping():
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def run_forever() -> None:
    settings = get_settings()
    queue = DownloadQueue(settings.redis_url)
    if settings.auto_create_db:
        init_database()
    repository = DownloadRepository()
    library_repository = LibraryRepository()
    last_readiness_check = 0.0
    while True:
        now_monotonic = asyncio.get_running_loop().time()
        if now_monotonic - last_readiness_check >= 5:
            _set_worker_ready(_dependencies_ready(queue))
            last_readiness_check = now_monotonic
        try:
            await process_once(queue, repository, library_repository=library_repository)
        except QueueUnavailable:
            _set_worker_ready(False)
            logger.error("Redis Streams unavailable; worker will retry without losing pending messages")
            await asyncio.sleep(2)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(run_forever())

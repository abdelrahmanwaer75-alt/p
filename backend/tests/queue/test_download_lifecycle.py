import asyncio
from collections import deque
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.extractors.base import DownloadResult, TransientDownloadError
from app.repositories.downloads import DownloadRepository
from app.repositories.library import LibraryRepository
from app.schemas.downloads import DownloadStatus, DownloadTaskCreate
from app.services.downloads import DownloadService
from worker import MAX_RETRIES, process_once


OWNER_A = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_B = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


class FakeQueue:
    def __init__(self, *, enqueue_ok: bool = True):
        self.enqueue_ok = enqueue_ok
        self.messages = deque()
        self.acked = []
        self.events = []
        self.retries = []
        self.dead_letters = []

    def enqueue(self, task_id, *, attempt=0):
        if not self.enqueue_ok:
            return None
        message = type("Message", (), {"message_id": str(uuid4()), "task_id": task_id, "attempt": attempt})()
        self.messages.append(message)
        return message.message_id

    def recover_pending(self, **kwargs):
        return []

    def dequeue(self, timeout=1):
        return self.messages.popleft() if self.messages else None

    def ack(self, message_id):
        self.acked.append(message_id)
        return True

    def publish_event(self, task_id, event, **payload):
        self.events.append((task_id, event, payload))
        return True

    def retry(self, message, *, delay_seconds, attempt):
        self.retries.append((message, delay_seconds, attempt))
        return self.enqueue(message.task_id, attempt=attempt)

    def dead_letter(self, message, *, reason, attempt):
        self.dead_letters.append((message.task_id, reason, attempt))
        self.ack(message.message_id)
        return True


class FakeExtractor:
    platform = "vimeo"
    available = True

    def __init__(self, behavior="complete"):
        self.behavior = behavior
        self.calls = 0

    async def download(self, task, progress_callback, cancellation_requested):
        self.calls += 1
        if self.behavior == "transient":
            raise TransientDownloadError("temporary source failure")
        await progress_callback(50, 100, 10.0, 5)
        if await cancellation_requested():
            raise TransientDownloadError("cancelled")
        return DownloadResult("/media/result.mp4", "result.mp4", 100, 100, "mp4", "video/mp4")


class FakeRegistry:
    def __init__(self, extractor):
        self.extractor = extractor

    def get(self, platform):
        return self.extractor if platform == "vimeo" else None


def payload() -> DownloadTaskCreate:
    return DownloadTaskCreate(
        source_url="https://vimeo.com/123456",
        platform="vimeo",
        title="Verified title",
        format_id="source-720p",
        format_type="video",
        extension="mp4",
        mime_type="video/mp4",
        quality="720p",
        authorized=True,
    )


def test_queue_creation_and_duplicate_idempotency():
    queue = FakeQueue()
    service = DownloadService(DownloadRepository(), queue, FakeRegistry(FakeExtractor()))
    key = "download-idempotency-1"
    first = service.create(payload(), OWNER_A, idempotency_key=key)
    second = service.create(payload(), OWNER_A, idempotency_key=key)
    assert first.id == second.id
    assert first.status == DownloadStatus.QUEUED
    assert len(queue.messages) == 1


def test_redis_failure_marks_task_failed_and_does_not_return_success():
    repository = DownloadRepository()
    service = DownloadService(repository, FakeQueue(enqueue_ok=False), FakeRegistry(FakeExtractor()))
    with pytest.raises(HTTPException) as error:
        service.create(payload(), OWNER_A)
    assert error.value.status_code == 503
    task = repository.list(OWNER_A)[0]
    assert task.status == DownloadStatus.FAILED
    assert task.error_code == "REDIS_UNAVAILABLE"


def test_worker_completes_and_writes_library_with_real_result():
    repository = DownloadRepository()
    queue = FakeQueue()
    extractor = FakeExtractor()
    service = DownloadService(repository, queue, FakeRegistry(extractor))
    task = service.create(payload(), OWNER_A)
    assert asyncio.run(process_once(queue, repository, library_repository=LibraryRepository(), extractor_registry=FakeRegistry(extractor), sleep=lambda _: None))
    completed = repository.get_any(task.id)
    assert completed is not None
    assert completed.status == DownloadStatus.COMPLETED
    assert completed.progress_percent == 100
    assert completed.output_path == "/media/result.mp4"
    library = LibraryRepository().list(OWNER_A)
    stored = next(item for item in library if item.media_path == "/media/result.mp4")
    assert stored.filename == "result.mp4"
    assert stored.mime_type == "video/mp4"
    assert stored.file_size == 100


def test_worker_transient_retry_and_dead_letter_after_three_retries():
    repository = DownloadRepository()
    queue = FakeQueue()
    extractor = FakeExtractor("transient")
    service = DownloadService(repository, queue, FakeRegistry(extractor))
    task = service.create(payload(), OWNER_A)
    for _ in range(MAX_RETRIES + 1):
        asyncio.run(process_once(queue, repository, extractor_registry=FakeRegistry(extractor), sleep=lambda _: None))
    final = repository.get_any(task.id)
    assert final is not None
    assert final.status == DownloadStatus.FAILED
    assert final.error_code == "RETRY_EXHAUSTED"
    assert len(queue.dead_letters) == 1


def test_cancellation_state_transitions_and_completed_rejection():
    repository = DownloadRepository()
    queue = FakeQueue()
    service = DownloadService(repository, queue, FakeRegistry(FakeExtractor()))
    queued = service.create(payload(), OWNER_A, idempotency_key="cancel-queued")
    assert service.cancel(queued.id, OWNER_A).status == DownloadStatus.CANCELLED

    running = service.create(payload(), OWNER_A, idempotency_key="cancel-running")
    repository.update(running.id, status=DownloadStatus.DOWNLOADING.value)
    assert service.cancel(running.id, OWNER_A).status == DownloadStatus.CANCELLING

    completed = service.create(payload(), OWNER_A, idempotency_key="cancel-completed")
    repository.update(completed.id, status=DownloadStatus.COMPLETED.value)
    with pytest.raises(HTTPException) as error:
        service.cancel(completed.id, OWNER_A)
    assert error.value.status_code == 409


def test_download_user_isolation_for_get_cancel_and_list():
    repository = DownloadRepository()
    queue = FakeQueue()
    service = DownloadService(repository, queue, FakeRegistry(FakeExtractor()))
    task = service.create(payload(), OWNER_A, idempotency_key="isolation")
    assert service.list(OWNER_B) == []
    with pytest.raises(HTTPException) as get_error:
        service.get(task.id, OWNER_B)
    assert get_error.value.status_code == 404
    with pytest.raises(HTTPException) as cancel_error:
        service.cancel(task.id, OWNER_B)
    assert cancel_error.value.status_code == 404


class CrashThenCompleteExtractor(FakeExtractor):
    def __init__(self):
        super().__init__()
        self.crashed = False

    async def download(self, task, progress_callback, cancellation_requested):
        if not self.crashed:
            self.crashed = True
            raise KeyboardInterrupt("simulated worker crash")
        return await super().download(task, progress_callback, cancellation_requested)


class PendingRecoveryQueue(FakeQueue):
    def __init__(self):
        super().__init__()
        self.delivered = False

    def dequeue(self, timeout=1):
        if self.delivered or not self.messages:
            return None
        self.delivered = True
        return self.messages[0]

    def recover_pending(self, **kwargs):
        if self.delivered and not self.acked and self.messages:
            return [self.messages[0]]
        return []


def test_worker_crash_leaves_message_pending_for_recovery():
    repository = DownloadRepository()
    queue = PendingRecoveryQueue()
    extractor = CrashThenCompleteExtractor()
    service = DownloadService(repository, queue, FakeRegistry(extractor))
    task = service.create(payload(), OWNER_A, idempotency_key="crash-recovery")
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(process_once(queue, repository, extractor_registry=FakeRegistry(extractor), sleep=lambda _: None))
    assert queue.acked == []
    asyncio.run(process_once(queue, repository, extractor_registry=FakeRegistry(extractor), sleep=lambda _: None))
    recovered = repository.get_any(task.id)
    assert recovered is not None
    assert recovered.status == DownloadStatus.COMPLETED

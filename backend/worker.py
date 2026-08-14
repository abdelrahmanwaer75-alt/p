import asyncio
import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.queue import DownloadQueue
from app.repositories.downloads import DownloadRepository
from app.schemas.downloads import DownloadStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vidora.worker")


async def process_once(queue: DownloadQueue, repository: DownloadRepository) -> bool:
    task_id = queue.dequeue(timeout=1)
    if task_id is None:
        return False
    task = repository.get_any(task_id)
    if task is None:
        logger.warning("Received unknown download task %s", task_id)
        return True
    failed = task.model_copy(update={
        "status": DownloadStatus.FAILED,
        "error_message": "No authorized download adapter is configured",
        "updated_at": datetime.now(timezone.utc),
    })
    repository.save(failed)
    logger.info("Task %s failed without an authorized adapter", task_id)
    return True


async def run_forever() -> None:
    settings = get_settings()
    queue = DownloadQueue(settings.redis_url)
    repository = DownloadRepository(settings.download_db_path)
    while True:
        await process_once(queue, repository)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(run_forever())

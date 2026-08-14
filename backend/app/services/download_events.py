from uuid import UUID

from app.queue.stream import DownloadQueue


class DownloadEventService:
    def __init__(self, queue: DownloadQueue) -> None:
        self.queue = queue

    def publish(self, task_id: UUID, event: str, **payload: object) -> bool:
        return self.queue.publish_event(task_id, event, **payload)

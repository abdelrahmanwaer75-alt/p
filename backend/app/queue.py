import json
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class DownloadQueue:
    queue_name = "vidora:downloads"

    def __init__(self, redis_url: str | None = None) -> None:
        self.redis = Redis.from_url(redis_url or get_settings().redis_url, decode_responses=True)

    def enqueue(self, task_id: UUID) -> bool:
        try:
            self.redis.rpush(self.queue_name, json.dumps({"task_id": str(task_id)}))
            return True
        except RedisError:
            return False

    def dequeue(self, timeout: int = 1) -> UUID | None:
        item = self.redis.blpop(self.queue_name, timeout=timeout)
        if not item:
            return None
        payload = json.loads(item[1])
        return UUID(payload["task_id"])

    def ping(self) -> bool:
        try:
            return bool(self.redis.ping())
        except RedisError:
            return False

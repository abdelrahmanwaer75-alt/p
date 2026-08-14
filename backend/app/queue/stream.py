from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError, ResponseError

from app.core.config import get_settings


class QueueUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class QueueMessage:
    message_id: str
    task_id: UUID
    attempt: int


class DownloadQueue:
    stream_name = "vidora:downloads:stream"
    group_name = "vidora:download-workers"
    dead_letter_stream = "vidora:downloads:dead-letter"
    event_stream = "vidora:downloads:events"

    def __init__(self, redis_url: str | None = None, consumer_name: str | None = None, redis_client: Redis | None = None) -> None:
        self.redis = redis_client or Redis.from_url(redis_url or get_settings().redis_url, decode_responses=True)
        self.consumer_name = consumer_name or f"worker-{socket.gethostname()}"

    def _ensure_group(self) -> None:
        try:
            self.redis.xgroup_create(self.stream_name, self.group_name, id="0-0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def enqueue(self, task_id: UUID, *, attempt: int = 0) -> str | None:
        try:
            self._ensure_group()
            return cast(
                str,
                self.redis.xadd(
                    self.stream_name,
                    {"task_id": str(task_id), "attempt": str(attempt), "enqueued_at": datetime.now(timezone.utc).isoformat()},
                    maxlen=10000,
                    approximate=True,
                ),
            )
        except RedisError:
            return None

    def dequeue(self, timeout: int = 1) -> QueueMessage | None:
        try:
            self._ensure_group()
            response = cast(
                Any,
                self.redis.xreadgroup(
                    self.group_name,
                    self.consumer_name,
                    {self.stream_name: ">"},
                    count=1,
                    block=max(timeout, 0) * 1000,
                ),
            )
            if not response:
                return None
            _, messages = response[0]
            message_id, fields = messages[0]
            return QueueMessage(message_id=message_id, task_id=UUID(fields["task_id"]), attempt=int(fields.get("attempt", 0)))
        except (RedisError, ValueError, KeyError) as exc:
            if isinstance(exc, RedisError):
                raise QueueUnavailable("Redis Streams is unavailable") from exc
            raise

    def ack(self, message_id: str) -> bool:
        try:
            return bool(self.redis.xack(self.stream_name, self.group_name, message_id))
        except RedisError:
            return False

    def retry(self, message: QueueMessage, *, delay_seconds: float, attempt: int) -> str | None:
        # The worker sleeps for the bounded backoff before publishing the retry entry.
        return self.enqueue(message.task_id, attempt=attempt)

    def dead_letter(self, message: QueueMessage, *, reason: str, attempt: int) -> bool:
        try:
            dead_letter_fields: dict[str, str | int | float] = {"task_id": str(message.task_id), "source_message_id": message.message_id, "attempt": str(attempt), "reason": reason}
            self.redis.xadd(
                self.dead_letter_stream,
                cast(Any, dead_letter_fields),
                maxlen=10000,
                approximate=True,
            )
            self.ack(message.message_id)
            return True
        except RedisError:
            return False

    def recover_pending(self, *, min_idle_ms: int = 60_000, count: int = 100) -> list[QueueMessage]:
        try:
            self._ensure_group()
            claimed = cast(
                Any,
                self.redis.xautoclaim(
                    self.stream_name,
                    self.group_name,
                    self.consumer_name,
                    min_idle_time=min_idle_ms,
                    start_id="0-0",
                    count=count,
                ),
            )
            entries = claimed[1] if claimed else []
            result: list[QueueMessage] = []
            for message_id, fields in entries:
                result.append(QueueMessage(message_id=message_id, task_id=UUID(fields["task_id"]), attempt=int(fields.get("attempt", 0))))
            return result
        except (RedisError, ValueError, KeyError) as exc:
            if isinstance(exc, RedisError):
                raise QueueUnavailable("Redis Streams is unavailable") from exc
            raise

    def publish_event(self, task_id: UUID, event: str, **payload: object) -> bool:
        try:
            event_name = {"queued": "download.created", "starting": "download.started", "started": "download.started", "progress": "download.progress", "completed": "download.completed", "failed": "download.failed", "cancelled": "download.cancelled"}.get(event, event if event.startswith("download.") else f"download.{event}")
            fields: dict[str, str | int | float] = {"task_id": str(task_id), "event": event_name, "published_at": datetime.now(timezone.utc).isoformat()}
            fields.update({key: json.dumps(value) if not isinstance(value, str) else value for key, value in payload.items()})
            self.redis.xadd(
                self.event_stream,
                cast(Any, fields),
                maxlen=10000,
                approximate=True,
            )
            return True
        except RedisError:
            return False

    def ping(self) -> bool:
        try:
            return bool(self.redis.ping())
        except RedisError:
            return False

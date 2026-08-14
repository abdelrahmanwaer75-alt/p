from uuid import UUID

from redis.exceptions import RedisError

from app.queue.stream import DownloadQueue, QueueMessage


TASK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class RedisFake:
    def __init__(self, *, ping_ok: bool = True):
        self.ping_ok = ping_ok
        self.entries: list[tuple[str, dict[str, str]]] = []
        self.acked: list[tuple[str, str, str]] = []
        self.dead_letters: list[tuple[str, dict[str, str]]] = []
        self.groups: list[tuple[str, str]] = []
        self.next_id = 0

    def ping(self) -> bool:
        if not self.ping_ok:
            raise RedisError("redis unavailable")
        return True

    def xgroup_create(self, stream: str, group: str, id: str, mkstream: bool) -> None:
        self.groups.append((stream, group))

    def xadd(self, stream: str, fields: dict[str, str], **_kwargs: object) -> str:
        self.next_id += 1
        message_id = f"{self.next_id}-0"
        if stream.endswith(":dead-letter"):
            self.dead_letters.append((message_id, fields))
        else:
            self.entries.append((message_id, fields))
        return message_id

    def xreadgroup(self, group: str, consumer: str, streams: dict[str, str], count: int, block: int) -> list[tuple[str, list[tuple[str, dict[str, str]]]]]:
        if not self.entries:
            return []
        message_id, fields = self.entries.pop(0)
        return [(next(iter(streams)), [(message_id, fields)])]

    def xack(self, stream: str, group: str, message_id: str) -> int:
        self.acked.append((stream, group, message_id))
        return 1

    def xautoclaim(self, stream: str, group: str, consumer: str, min_idle_time: int, start_id: str, count: int) -> tuple[str, list[tuple[str, dict[str, str]]], list[str]]:
        return ("0-0", [], [])


def test_stream_queue_ack_retry_and_dead_letter():
    redis = RedisFake()
    queue = DownloadQueue(redis_client=redis, consumer_name="test-worker")
    message_id = queue.enqueue(TASK_ID, attempt=0)
    assert message_id is not None
    message = queue.dequeue(timeout=0)
    assert isinstance(message, QueueMessage)
    assert message.task_id == TASK_ID
    assert queue.ack(message.message_id)
    retried = queue.retry(message, delay_seconds=2, attempt=1)
    assert retried is not None
    assert queue.dead_letter(message, reason="permanent", attempt=3)
    assert redis.dead_letters
    assert queue.recover_pending(count=10) == []


def test_stream_queue_reports_redis_ping_failure():
    queue = DownloadQueue(redis_client=RedisFake(ping_ok=False))
    assert queue.ping() is False

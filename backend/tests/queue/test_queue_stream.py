from uuid import UUID

from redis.exceptions import RedisError

from app.queue.stream import DownloadQueue, QueueMessage


TASK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class RedisFake:
    def __init__(self, *, ping_ok: bool = True):
        self.ping_ok = ping_ok
        self.entries = []
        self.acked = []
        self.dead_letters = []
        self.groups = []
        self.next_id = 0

    def ping(self):
        if not self.ping_ok:
            raise RedisError("redis unavailable")
        return True

    def xgroup_create(self, stream, group, id, mkstream):
        self.groups.append((stream, group))

    def xadd(self, stream, fields, **_kwargs):
        self.next_id += 1
        message_id = f"{self.next_id}-0"
        if stream.endswith(":dead-letter"):
            self.dead_letters.append((message_id, fields))
        else:
            self.entries.append((message_id, fields))
        return message_id

    def xreadgroup(self, group, consumer, streams, count, block):
        if not self.entries:
            return []
        message_id, fields = self.entries.pop(0)
        return [(next(iter(streams)), [(message_id, fields)])]

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))
        return 1

    def xautoclaim(self, stream, group, consumer, min_idle_time, start_id, count):
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

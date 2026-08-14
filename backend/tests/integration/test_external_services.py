"""Integration checks for CI-provided PostgreSQL and Redis services.

The tests are skipped in ordinary local runs unless both service URLs are set.
CI supplies real PostgreSQL and Redis containers, so these checks never replace
service integration with fakes.
"""

import os
import uuid

import pytest
from redis import Redis
from sqlalchemy import create_engine, text

from app.queue import DownloadQueue

DATABASE_URL = os.getenv("VIDORA_CI_DATABASE_URL")
REDIS_URL = os.getenv("VIDORA_CI_REDIS_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not REDIS_URL,
    reason="VIDORA_CI_DATABASE_URL and VIDORA_CI_REDIS_URL are required",
)


def test_postgresql_connection_is_real() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    engine.dispose()


def test_redis_stream_group_ack_retry_dead_letter_and_event() -> None:
    assert REDIS_URL is not None
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    assert redis.ping() is True

    queue = DownloadQueue(redis_url=REDIS_URL, consumer_name=f"ci-{uuid.uuid4()}")
    task_id = uuid.uuid4()
    first_id = queue.enqueue(task_id)
    assert first_id is not None

    message = queue.dequeue(timeout=1)
    assert message is not None
    assert message.task_id == task_id
    assert queue.ack(message.message_id) is True

    retry_id = queue.retry(message, delay_seconds=0, attempt=1)
    assert retry_id is not None
    retry_message = queue.dequeue(timeout=1)
    assert retry_message is not None
    assert retry_message.attempt == 1
    assert queue.dead_letter(retry_message, reason="ci-check", attempt=3) is True

    assert queue.publish_event(task_id, "progress", progress_percent=25) is True
    event_entries = redis.xrange(queue.event_stream, count=20)
    assert any(
        fields.get("task_id") == str(task_id)
        and fields.get("event") == "download.progress"
        for _, fields in event_entries
    )

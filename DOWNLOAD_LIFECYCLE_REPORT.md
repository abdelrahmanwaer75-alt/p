# Vidora Download Lifecycle Report

**Repository:** Existing Vidora repository, continued in place
**Scope:** Truthful download lifecycle architecture
**Actual downloading:** Not available because no approved platform download extractor is implemented
**Remote Git push:** Not performed

## Lifecycle implementation

The download flow now persists a complete task record, queues only through Redis Streams, processes messages through a worker consumer-group contract, and records truthful state transitions. No fake progress, fabricated output, simulated file, or pretend completion was added.

| Stage | Behavior |
|---|---|
| Analyze and select | The API accepts platform and selected-format metadata in `DownloadTaskCreate`; the existing analyzer remains the source of platform/format truth |
| Task creation | The task is persisted before queueing and carries platform, title, format, MIME, extension, quality, progress, output, error, retry, and lifecycle timestamps |
| Queueing | Redis Streams `XADD` is used with a consumer group; queue failure marks the task `failed` with `REDIS_UNAVAILABLE` and returns HTTP 503 rather than claiming success |
| Worker claim | The worker reads through `XREADGROUP`, acknowledges only after durable handling, and reclaims sufficiently idle pending messages with `XAUTOCLAIM` |
| Extractor gate | Missing or unavailable platform adapters produce `FEATURE_NOT_AVAILABLE`; the worker never creates output or progress for an unavailable adapter |
| Progress | Only an actual extractor callback may update bytes, total bytes, percentage, speed, ETA, and events |
| Completion | A real extractor result is persisted with output path/filename and the completed media is inserted into the authenticated user’s library |
| Failure | Permanent failures become `failed` with explicit error codes; transient failures use bounded exponential retry |
| Cancellation | Queued tasks become `cancelled`; active tasks become `cancelling` and the worker finalizes them as `cancelled`; completed tasks reject cancellation |

## DATABASE

Alembic migration `0003_download_lifecycle` extends the existing schema with the requested task fields: `id`, `user_id`, `source_url`, `platform`, `title`, `format_id`, `format_type`, `extension`, `mime_type`, `quality`, `status`, `progress_percent`, `bytes_downloaded`, `total_bytes`, `speed`, `eta`, `output_path`, `output_filename`, `error_code`, `error_message`, `created_at`, `started_at`, `completed_at`, `cancelled_at`, `updated_at`, plus retry count and an idempotency key. The migration backfills `user_id` from the legacy owner column and adds ownership/index constraints without destroying compatibility with existing data.

The API schema exposes the existing `owner_id` response name for compatibility, while persistence uses the requested `user_id` field. Ownership is always derived from the authenticated user in service and repository methods.

The lifecycle status set is:

`queued`, `starting`, `downloading`, `paused`, `cancelling`, `completed`, `failed`, and `cancelled`.

## QUEUE

The previous raw list/BLPOP queue was replaced with Redis Streams. The queue defines a stream, consumer group, consumer name, dead-letter stream, and event stream. Each message carries a task ID, attempt number, and enqueue timestamp. Messages are acknowledged only after the task reaches a durable handled state.

Pending messages can be reclaimed after an idle threshold through `XAUTOCLAIM`, preventing a worker crash from permanently losing a download. Transient retry scheduling publishes a replacement message before acknowledging the original message, preventing the acknowledgement order from creating a loss window. Failed retry exhaustion is sent to the dead-letter stream.

## WORKER

The worker validates terminal and cancellation states, records `starting` and `downloading`, resolves the platform extractor, calls only an implemented extractor download method, persists real progress callbacks, checks cancellation, saves the actual extractor result, and creates the library record only after completion. If there is no available authorized extractor, it writes `FEATURE_NOT_AVAILABLE` and acknowledges the queue message without creating fake output.

Transient failures are retried at most three times with exponential delays of 1, 2, and 4 seconds, capped at 30 seconds. Permanent failures are not retried indefinitely. Worker crash recovery is covered by pending-message handling, and the worker does not reclaim active messages immediately; only sufficiently idle messages are eligible for recovery.

## API

Existing authenticated download endpoints remain available. `POST /api/v1/downloads` now accepts an optional `Idempotency-Key` header and refuses unavailable extractors with HTTP 501 and `FEATURE_NOT_AVAILABLE`. `GET /api/v1/downloads`, `GET /api/v1/downloads/{id}`, and the existing run/requeue endpoint remain owner-scoped. A new `POST /api/v1/downloads/{id}/cancel` endpoint implements cancellation semantics and rejects completed tasks with HTTP 409.

Duplicate requests carrying the same idempotency key for the same authenticated user return the existing task and do not enqueue a second message. A different user cannot retrieve, cancel, or list another user’s tasks.

## TESTS

| Test area | Result |
|---|---:|
| Full `pytest -q` | **50 passed** |
| Queue creation | Passed with idempotency protection |
| Redis failure | Passed; task becomes `failed/REDIS_UNAVAILABLE` and API does not return success |
| Worker completion | Passed with real extractor result contract and library insertion |
| Missing extractor | Passed; `FEATURE_NOT_AVAILABLE`, no output or fake progress |
| Transient retry | Passed with bounded retries and dead-letter handling |
| Worker crash/pending recovery | Passed |
| Queued cancellation | Passed: `queued → cancelled` |
| Active cancellation | Passed: `downloading → cancelling` |
| Completed cancellation | Passed: rejected with conflict |
| User isolation | Passed for list, get, cancel, and idempotency ownership |
| Alembic migration | Passed through `0003_download_lifecycle (head)` |
| Schema verification | Passed for all required lifecycle columns |
| Python compilation and diff hygiene | Passed |

One existing Starlette/httpx deprecation warning remains and does not fail the suite.

## FILES CHANGED

| File | Change |
|---|---|
| `backend/app/db.py` | Expanded lifecycle task model and indexes |
| `backend/alembic/versions/0003_download_lifecycle.py` | Added lifecycle schema migration and user_id backfill |
| `backend/app/schemas/downloads.py` | Added lifecycle statuses, metadata, progress, output, errors, retry, and cancellation contracts |
| `backend/app/repositories/downloads.py` | Added lifecycle persistence, owner isolation, idempotency, progress/update, and cancellation operations |
| `backend/app/queue.py` | Replaced BLPOP with Redis Streams consumer groups, ack, retry, pending recovery, DLQ, and events |
| `backend/app/extractors/base.py` | Added explicit download result and download capability boundary |
| `backend/app/services/downloads.py` | Added extractor preflight, Redis failure handling, idempotency, requeue, and cancellation |
| `backend/app/main.py` | Added idempotency header support and cancel endpoint |
| `backend/worker.py` | Implemented lifecycle worker, progress callbacks, retries, cancellation, feature gating, completion, and library insertion |
| `backend/tests/test_download_lifecycle.py` | Added queue, retry, crash recovery, cancellation, completion, duplicate, and isolation tests |
| `backend/tests/test_api.py` | Updated obsolete fake-progress expectation to truthful feature-unavailable behavior |
| `backend/tests/test_auth_security.py` | Updated download isolation expectation for unavailable extractors |
| `AUDIT.md` | To be synchronized with this lifecycle phase |

## REMAINING

Actual downloading remains unavailable until an approved platform adapter implements the extractor `download()` contract for a supported platform. That adapter must provide verified output, real progress callbacks, cancellation cooperation, transient/permanent error classification, secure output paths, and platform/legal authorization. Redis/PostgreSQL runtime integration tests should run in CI against real services, and production should add queue lag monitoring, dead-letter operations, expired-message cleanup, and worker concurrency/load testing.

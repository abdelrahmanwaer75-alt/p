# Vidora Final QA and Production Audit

## Scope

This audit covers the current Vidora repository after database and authentication work, safe media analysis, download lifecycle, Flutter integration, file management, player and playlist work, background-download bridges, and the security hardening pass. The project was continued in place; working code was not intentionally rewritten or removed.

## Project status matrix

| Area | Status | Assessment |
|---|---|---|
| Architecture | PARTIALLY READY | Backend, Flutter feature structure, storage, queue, and mobile integration boundaries exist. Full device and infrastructure validation remains required. |
| Backend | PARTIALLY READY | FastAPI routes, schemas, error handling, request IDs, rate limiting, security headers, auth dependencies, analyzer, downloads, files, library, and playlists are implemented and tested. |
| Flutter | PARTIALLY READY | Riverpod, GoRouter, typed models, API client, WebSocket state updates, player state, playlists, and background bridges are present. Flutter commands were not executable in this sandbox because Flutter/Dart were unavailable. |
| Database | PARTIALLY READY | SQLAlchemy 2.x models and Alembic migrations are present, with PostgreSQL production configuration and SQLite test fallback. Live PostgreSQL connection, migration upgrade, and rollback were not executable because Docker and `psql` were unavailable. |
| Queue | PARTIALLY READY | Redis Streams consumer groups, acknowledgement, retry, pending recovery, dead-letter behavior, and failure handling are covered by backend tests. A live Redis integration run was unavailable because Docker and `redis-cli` were unavailable. |
| Downloader | NOT READY | No approved platform download adapter is enabled. The worker returns `FEATURE_NOT_AVAILABLE` rather than faking downloads, progress, formats, or files. |
| Player | PARTIALLY READY | `media_kit` integration and player state boundaries exist. Physical media playback and platform compilation require Flutter SDK/device validation. |
| File Manager | PARTIALLY READY | Managed-root storage operations, path-traversal protections, metadata, rename, move, delete, and library synchronization are implemented. Real mobile permission and share/open behavior require device testing. |
| Playlists | PARTIALLY READY | CRUD, item management, ordering, ownership checks, and Flutter feature surfaces are implemented and covered by backend tests. Device UI validation remains. |
| Authentication | READY for backend integration | Argon2 password hashing, access/refresh JWT validation, issuer/audience/expiration checks, refresh rotation, revocation, logout, current-user lookup, and user isolation are implemented. |
| Security | PARTIALLY READY | SSRF, file confinement, rate limiting, CORS configuration, security headers, non-root containers, secret validation, and redacted structured logging are implemented. External penetration testing and live deployment review remain. |
| Testing | PARTIALLY READY | Backend suite and Python compilation passed. Flutter, lint/type checks, Docker runtime, PostgreSQL runtime, Redis runtime, and device E2E checks were unavailable in this environment. |
| Docker | PARTIALLY READY | Compose and Dockerfile statically contain non-root users, read-only roots, capability drops, no-new-privileges, health checks, and restart policies. Docker build and startup were not run because Docker was unavailable. |
| CI/CD | NOT READY | No verified CI pipeline currently runs the complete Flutter, backend lint/type, database, Redis, Docker, and mobile matrix. |

## Verification executed

| Check | Result |
|---|---:|
| Backend `pytest -q` on a clean local test database | **63 passed** |
| Python `compileall` for backend application, tests, and worker | Passed |
| Security-focused tests | Included in the passing 63-test suite |
| Authentication and user-isolation tests | Passed within the suite |
| SSRF and path-traversal tests | Passed within the suite |
| Queue retry, acknowledgement, recovery, cancellation, and failure tests | Passed within the suite |
| `git diff --check` | Pending final pre-commit check |
| Flutter `pub get`, format, analyze, test | Not run: Flutter/Dart unavailable |
| `ruff check .` | Not run: Ruff unavailable and no repository Ruff configuration found |
| `mypy .` | Not run: mypy unavailable and no repository mypy configuration found |
| Alembic against live PostgreSQL and rollback | Not run: PostgreSQL/Docker unavailable |
| Redis live integration | Not run: Redis/Docker unavailable |
| Docker Compose config/build/up | Not run: Docker unavailable |
| Android/iOS device validation | Not run: platform SDKs/devices unavailable |

## Completed

The repository includes production-oriented authentication, user isolation, migration-driven schema management, safe platform analysis, reliable queue lifecycle primitives, managed filesystem operations, playlist ownership enforcement, Flutter session/API/WebSocket integration, mobile background bridges, centralized security middleware, non-root container configuration, and security documentation.

## Fixed in final QA phase

The README was rewritten to remove stale Phase 1 and SQLite-only claims and now reflects the actual current status. This audit was updated with verified test counts and explicit unavailable-tool limitations. The environment template documents production requirements while retaining placeholders. The final security documentation remains in `SECURITY.md`.

## Remaining work

The remaining work is primarily environment and integration validation: install Flutter/Dart and run the mobile checks; install or provision Ruff and mypy; run Alembic against PostgreSQL; run Redis Streams against a real Redis service; build and start the Compose stack; validate `/health` and `/ready` under dependency failure; execute Android/iOS device tests; and add CI/CD for these checks.

The actual media downloader remains intentionally disabled until each allowlisted platform has an approved, authorized, policy-compliant adapter with verified output, real progress, cancellation cooperation, secure file handling, and transient/permanent error classification.

## Production blockers

Vidora must not be described as fully production-ready until the following blockers are closed: an approved real downloader implementation, live PostgreSQL and Redis integration validation, successful Docker build/start validation, Flutter analyze/test and device validation, CI/CD coverage, and external security testing. These limitations are explicit and the application must continue to report unavailable functionality honestly.

Last reviewed: 2026-08-14

## Flutter refactor QA update

The Flutter root was reorganized without rebuilding the application. `main.dart` now only initializes Flutter/media dependencies and calls `runApp`. `app.dart` owns `MaterialApp.router`, theme mode, locale, and global background-event handling. Navigation now lives under `lib/navigation`, configuration under `lib/config`, shared theme/API boundaries under `lib/core`, and controllers were moved beside analyzer, downloads, files, library, and settings features. The existing `features/providers.dart` file is a compatibility barrel only.

| Flutter check | Result |
|---|---:|
| `flutter pub get` | Passed |
| `dart format lib test` | Passed |
| `flutter analyze` | **No issues found** |
| Full `flutter test` | **All tests passed** |
| `libmpv` dependency for media_kit tests | Installed in QA sandbox |

The widget test was made deterministic by providing a test API client and test router; it still verifies onboarding and navigation to login. The full test suite includes player state validation. Physical Android/iOS builds, permissions, notifications, background execution, and real device playback remain deployment-environment checks.

## Backend modularization QA update

The backend was reorganized in place. `main.py` is now wiring-only; route handlers are grouped under `app/api/routes`, shared dependencies under `app/api/dependencies.py`, business logic boundaries under `app/services`, database access under `app/repositories` and `app/db`, Redis Streams under `app/queue`, filesystem access under `app/storage`, and worker execution under `app/workers`. The legacy `backend/worker.py`, `app/db`, `app.queue`, `app.security`, and config import paths remain compatible through thin exports.

| Backend check | Result |
|---|---:|
| `python3 -m compileall -q backend` | Passed |
| `PYTHONPATH=backend pytest -q` | **65 passed** |
| Main route decorator scan | No business route decorators remain in `main.py` |
| Route raw Redis/filesystem/database scan | No direct infrastructure implementation in route modules |
| Extractor layout | Platform-specific subpackages for Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch |
| Test layout | Tests grouped under api, services, repositories, queue, security, and integration |

The only test output warning is an upstream Starlette/httpx deprecation warning. Runtime Docker, PostgreSQL, Redis, and device-level deployment checks remain environment-specific.

## Database and persistent media storage hardening update

Production database configuration now rejects SQLite, disables `AUTO_CREATE_DB`, and uses PostgreSQL through the same `DATABASE_URL` in API and worker Compose services. SQLAlchemy uses `pool_pre_ping` plus configurable pool size, overflow, timeout, and recycle settings. Alembic normalizes async PostgreSQL URLs, enables type comparison, and runs each migration transactionally where the backend supports it.

`MediaStorage` is the named storage boundary over the existing safe filesystem implementation. It derives its default root from `DOWNLOAD_DIRECTORY`, provides `save`, `delete`, `move`, `rename`, `exists`, `get_path`, and `get_metadata`, and canonicalizes paths to reject absolute escapes, traversal, and symlink escapes. Compose now mounts the persistent `media_data` named volume into both API and worker while retaining a read-only container root.

The API exposes `/health` for liveness and `/ready` for PostgreSQL/Redis readiness. The worker writes `/tmp/vidora-worker.ready` only after both dependencies respond, and the worker healthcheck verifies marker freshness. Docker validation could not run because Docker is not installed in the execution environment; Compose configuration was reviewed statically.

| Validation | Result |
|---|---:|
| `PYTHONPATH=backend pytest -q` | **68 passed** |
| `python3 -m compileall -q backend` | Passed |
| `alembic upgrade head` on isolated SQLite test database | Passed through revision `0006` |
| `git diff --check` | Passed |
| Docker Compose config/build | Not run: Docker unavailable |

## Download lifecycle hardening update

The download lifecycle now has a central transition policy and explicit service boundaries for state machine, retry policy, events, queue, and repository access. Redis Streams supports consumer groups, acknowledgement, retry enqueueing, pending recovery, dead-lettering, and event publishing. The worker preserves pending messages across uncaught crashes, retries only `TransientDownloadError` up to three times, and marks permanent or unavailable-adapter failures without endless retries.

Progress events are derived from extractor callbacks. If an adapter cannot report total bytes, the event contains downloaded bytes but no fabricated percentage. Pause and resume are explicitly unavailable until native adapter support exists. Ownership and idempotency behavior remains scoped to the authenticated user.

| Lifecycle validation | Result |
|---|---:|
| Full backend suite | **72 passed** |
| Queue ack/retry/dead-letter/ping tests | Passed |
| Worker crash and pending recovery tests | Passed |
| User isolation and duplicate idempotency tests | Passed |
| `python3 -m compileall -q backend` | Passed |
| `git diff --check` | Passed |

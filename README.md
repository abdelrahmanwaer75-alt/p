# Vidora

Vidora is a Flutter client and FastAPI backend for authorized media analysis, download lifecycle management, local file management, media playback, and playlists. The project is continued in place and intentionally does not bypass DRM, CAPTCHA, paywalls, authentication, anti-bot controls, or platform restrictions.

## Project status

The application has a production-oriented architecture, but it is **not yet a fully production-ready downloader** because approved platform download adapters are not implemented. The backend refuses unavailable download execution with `FEATURE_NOT_AVAILABLE`; it does not fabricate metadata, formats, progress, or output files.

| Area | Status | Notes |
|---|---|---|
| Backend API | Partially ready | FastAPI routes, typed schemas, unified errors, request IDs, security middleware, and OpenAPI are implemented. |
| Authentication | Ready for integration testing | Argon2 passwords, access/refresh JWTs, rotation, revocation, issuer/audience/expiration checks, and protected user-scoped routes are implemented. |
| Database | Partially ready | SQLAlchemy 2.x and Alembic migrations target PostgreSQL in production; SQLite is used for local tests. |
| Queue and worker | Partially ready | Redis Streams, consumer groups, acknowledgement, retry, pending recovery, dead-letter handling, and truthful state transitions are covered by tests. |
| Downloader | Not ready for production | No approved platform download adapter is enabled. |
| Flutter integration | Partially ready | Riverpod, GoRouter, typed API models, WebSocket download updates, player, playlists, and background bridges are present; Flutter SDK validation was unavailable in this sandbox. |
| Docker | Configuration ready | API and worker use non-root UID/GID, read-only roots, dropped capabilities, health checks, and restart policies. Runtime build/up validation requires Docker. |

## Supported analysis platforms

The analysis allowlist contains only Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch. Unsupported platforms and invalid URLs are rejected. Analysis protects against localhost, private, reserved, link-local, metadata, invalid-scheme, and `file://` targets, with DNS-rebinding checks before outbound access.

## Local setup

The backend requires Python 3.12 or a compatible Python environment. Install dependencies and run the API from the repository root:

```bash
cd vidora/backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Copy `backend/.env.example` to the deployment environment and replace every placeholder. Production must use PostgreSQL, `AUTO_CREATE_DB=false`, an explicit `ALLOWED_ORIGINS` list, protected Redis, and a randomly generated `JWT_SECRET` of at least 32 characters. Never commit `.env` files or real credentials.

## Flutter setup

On a machine with Flutter and the required platform SDKs installed:

```bash
flutter pub get
dart format .
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://<host>:8000
```

Do not hardcode `127.0.0.1:8000` for physical devices. Use an API base URL appropriate to the Android emulator, iOS simulator, local network, or production deployment. Android background work is subject to WorkManager constraints, and iOS background URLSession execution is subject to Apple scheduling and networking policies.

## Docker

The Compose file provisions API, worker, PostgreSQL, and Redis. It requires `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `JWT_SECRET` from the environment:

```bash
export POSTGRES_USER=vidora
export POSTGRES_PASSWORD='<secret from a secret manager>'
export POSTGRES_DB=vidora
export JWT_SECRET='<long random production secret>'
docker compose -f infrastructure/docker-compose.yml config
docker compose -f infrastructure/docker-compose.yml up --build
```

The API applies Alembic migrations before starting. PostgreSQL and Redis should remain on private networks and should not be exposed directly to the public Internet.

## Health endpoints

`GET /health` reports process health. `GET /ready` checks application dependencies and should be used by deployment probes. Dependency failures must be treated as unavailable rather than reported as successful readiness.

## Testing

The verified sandbox command is:

```bash
rm -f backend/data/vidora_dev.db
PYTHONPATH=backend pytest -q
python3 -m compileall -q backend/app backend/tests backend/worker.py
```

The current result is **63 passed** and successful Python compilation. Flutter, Docker, PostgreSQL runtime, Redis runtime, `ruff`, and `mypy` could not be executed in this sandbox because their executables or platform toolchains are unavailable. They remain required CI or developer-machine checks.

## Documentation

Further implementation and QA details are documented in `AUDIT.md`, `SECURITY.md`, `DATABASE_AUTH_REPORT.md`, `MEDIA_ANALYSIS_REPORT.md`, `DOWNLOAD_LIFECYCLE_REPORT.md`, `DOWNLOAD_FILE_MANAGER_REPORT.md`, `MEDIA_PLAYER_PLAYLIST_REPORT.md`, `BACKGROUND_DOWNLOAD_REPORT.md`, and `FLUTTER_INTEGRATION_REPORT.md`.

## Legal and safety boundary

Vidora must only process media the user is authorized to download and the source platform permits downloading. DRM circumvention, paywall bypass, authentication bypass, CAPTCHA bypass, anti-bot bypass, private-content extraction without authorization, and arbitrary shell execution are excluded by design.

## Flutter architecture

The Flutter application is organized around a small `lib/main.dart`, `lib/app.dart` for the MaterialApp/router root, `config` and `navigation` boundaries, a core API/config/theme layer, and feature-owned controllers. Analyzer, downloads, files, library collections, settings, playlists, player, and authentication logic remain in their respective feature directories. `features/providers.dart` is retained only as a compatibility export barrel; it no longer contains the controller implementations.

The widget layer consumes Riverpod state and does not call Dio, WebSocket, or native method channels directly. API and background service implementations remain behind core/network and core/downloads boundaries.

## Latest Flutter verification

With the local Flutter SDK and `libmpv` available, the following checks passed:

```bash
flutter pub get
dart format lib test
flutter analyze
flutter test
```

The complete Flutter test suite passed. Android/iOS device builds and runtime background execution still require their platform SDKs, simulators/devices, and signing environments.

## Backend architecture

The backend now follows the same modular boundaries as the Flutter client. `app/main.py` is limited to application construction, middleware, exception handlers, lifespan, router registration, and health wiring. API routes live under `app/api/routes`, shared authentication and service dependencies under `app/api/dependencies.py`, business services under `app/services`, repositories under `app/repositories`, and SQLAlchemy boundaries under `app/db`.

Redis Streams is isolated under `app/queue`, filesystem access under `app/storage`, and worker execution under `app/workers/download_worker.py`; `backend/worker.py` remains a compatibility entrypoint. Platform extractors now live in per-platform subpackages. Existing legacy imports remain available through compatibility exports so the refactor does not change public behavior.

Backend QA after the modularization passed with `65 passed`; `python3 -m compileall -q backend` also passed. The suite retains one upstream Starlette/httpx deprecation warning that does not affect test results.

## Database and persistent storage hardening

Production uses PostgreSQL as the shared source of truth for the API and worker. SQLAlchemy now enables PostgreSQL connection pooling with pre-ping, bounded overflow, timeout, and recycle settings. SQLite remains available only for isolated development and tests; production settings reject SQLite and disable `AUTO_CREATE_DB`, while Alembic remains the schema authority.

Media files use the `MediaStorage` boundary and the configured `DOWNLOAD_DIRECTORY`. The production Compose deployment mounts the same named `media_data` volume into both API and worker at `/app/data/media`, alongside persistent PostgreSQL and Redis volumes. The application keeps a read-only container root while the media volume and `/tmp` remain writable where needed.

`/health` is a liveness endpoint. `/ready` verifies both PostgreSQL and Redis and returns HTTP 503 when either dependency is unavailable. The worker writes a readiness marker only after it can reach both PostgreSQL and Redis; its container healthcheck validates the marker freshness rather than merely checking that Python started.

## Download lifecycle hardening

Download processing now has an explicit state machine for queued, starting, downloading, completed, cancelling, cancelled, failed, and retry-to-queued paths. Redis Streams remains the reliability boundary with consumer groups, acknowledgement, pending-message recovery through `XAUTOCLAIM`, transient retry scheduling, dead-letter handling, and lifecycle event publishing.

The worker only reports progress received from an extractor callback. When an adapter does not provide a total size, it emits bytes downloaded without inventing a percentage. Unavailable adapters fail with `FEATURE_NOT_AVAILABLE`; no download or progress is simulated. Pause and resume return `FEATURE_NOT_AVAILABLE` until an extractor exposes native pause support rather than pretending that a state-only toggle pauses I/O.

Idempotency remains scoped to the authenticated owner and `Idempotency-Key`, cancellation is ownership-scoped, and failed transient processing is capped at three retries with bounded exponential backoff. A worker crash leaves the Redis message pending for recovery instead of acknowledging it prematurely.

## Media analyzer architecture

The analyzer uses isolated platform packages under `backend/app/extractors/reddit`, `vimeo`, `dailymotion`, `soundcloud`, and `twitch`. The registry allowlist contains only those five platforms; prohibited services such as YouTube, Instagram, Facebook, TikTok, and X/Twitter resolve to an unsupported generic result.

Analyzer results expose verified metadata and format fields including bitrate, resolution, fps, size, duration, MIME type, extension, quality, restrictions, and limitations. Unconfigured adapters return `supported=false`, `FEATURE_NOT_AVAILABLE`, empty format lists, and null metadata. The system never fabricates metadata, formats, sizes, durations, progress, or download URLs.

Both `/api/v1/analyze` and `/api/v1/analyzer/preview` delegate to the same analyzer service. Public URL validation rejects invalid schemes, embedded credentials, localhost, private/loopback/reserved/link-local/metadata addresses, and unsafe DNS answers. Adapter implementations must reuse the validated resolution result to prevent DNS rebinding between validation and outbound access.

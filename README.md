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

## Final production-hardening status

The repository has completed a focused production-hardening review without adding unsupported downloader behavior or rewriting working application flows. `ARCHITECTURE.md` documents the feature boundaries, backend service/repository layering, Redis Streams worker flow, analyzer boundary, storage controls, and deployment responsibilities.

The final security baseline includes Argon2 password hashing, short-lived access JWTs, refresh-token rotation and revocation, issuer/audience/expiration validation, request IDs, explicit error responses, security headers, rate limiting, strict CORS production validation, SSRF and DNS-rebinding defenses, canonical managed-storage paths, symlink/traversal protection, and authenticated user isolation.

CI now runs backend tests, Python compilation, Ruff, mypy, Alembic migrations against PostgreSQL, Flutter dependency/code-generation checks when configured, format checks, analyze, tests, Docker Compose configuration validation, and backend image build. The workflow intentionally does not fabricate mobile-device verification: Android/iOS builds, signing, notification rendering, OS background scheduling, and production network controls require their respective SDKs, devices, credentials, and deployment environment.

The Android release configuration no longer signs release artifacts with debug keys. A real release keystore must be injected by the deployment environment before publishing an Android release. This is an intentional blocker rather than a hidden insecure default.

## Final QA reporting rule

A green sandbox test run does not by itself establish production readiness. Production deployment remains blocked until the release keystore, protected PostgreSQL and Redis deployment, TLS/reverse-proxy policy, external egress controls, encrypted backups and restore tests, dependency/image scans, observability, and platform-specific Android/iOS validation are completed and accepted by the operator.

## Production infrastructure verification

A current repository inspection confirms that the Compose stack defines four services: API, worker, PostgreSQL, and Redis. API and worker use the same PostgreSQL connection pattern and Redis service address, while both mount the same persistent writable `media_data` volume at `/app/data/media`. Production schema creation is disabled and the API starts through `alembic upgrade head` before Uvicorn.

The API healthcheck calls `GET /health`, which is liveness-only. `GET /ready` checks both PostgreSQL and Redis and returns an unavailable response when either dependency fails. The worker does not use a fake print-based healthcheck: it writes `/tmp/vidora-worker.ready` only after database and Redis checks succeed, and the Compose healthcheck verifies the marker freshness.

The containers use non-root UID/GID `10001:10001`, read-only roots, `/tmp` tmpfs, dropped capabilities, `no-new-privileges`, persistent service volumes, dependency health conditions, and restart policies. Docker runtime communication, image build, and live service health could not be executed in the sandbox because Docker was unavailable; these checks are configured in CI and remain deployment verification items.

## CI/CD validation

GitHub Actions runs on every push and pull request. The workflow contains separate backend, PostgreSQL/Redis integration, Flutter, Docker, and repository-security jobs. Backend validation installs the project dependencies plus Ruff, mypy, and pip-audit; it runs compileall, pytest, linting, type checking, and dependency auditing without silently ignoring failures.

The integration job starts real PostgreSQL 16 and Redis 7 service containers, applies Alembic migrations against PostgreSQL, and runs integration checks that connect to the actual database and Redis Streams. The Redis checks exercise consumer-group creation, enqueue/dequeue, acknowledgement, retry, dead-letter handling, and event publishing.

Flutter CI runs `flutter pub get`, committed Freezed/json_serializable code generation through build_runner, strict Dart formatting, `flutter analyze`, and `flutter test`. Docker CI validates Compose configuration with CI-only variables and builds the backend image. Security CI runs repository secret scanning and Trivy filesystem vulnerability/secret/misconfiguration scanning.

The repository's `main` branch currently does not have GitHub branch protection configured; the GitHub API reported that the branch is not protected. Branch protection was not enabled automatically because repository permissions did not establish that it could be safely configured. Required checks are nevertheless defined in the workflow and run for pull requests.

## CI reliability update

The CI pipeline was validated against the current source rather than previous reports. Freezed model declarations now use the required generated mixins, the stale unused `models.g.dart` part was removed, and `dart run build_runner build` succeeds before Flutter analysis and tests. The generated `models.freezed.dart` output is committed and refreshed by CI.

The backend test dependency now requires a non-vulnerable pytest release range. Ruff runs an explicit E4/E7/E9/F baseline with documented compatibility-export exceptions, mypy runs against the typed core/database/storage layers, and pip-audit checks only the declared backend requirements manifest. The PostgreSQL/Redis integration job uses real service containers and the dedicated integration test is skipped only in ordinary local runs where those service URLs are not provided.

For the exact per-platform authorized download status and the conditions required before enabling an adapter, see [`AUTHORIZED_DOWNLOAD_REPORT.md`](AUTHORIZED_DOWNLOAD_REPORT.md).

For the complete authentication, JWT, authorization, rate-limit, WebSocket isolation, and sensitive-logging audit, see [`AUTH_SECURITY_AUDIT.md`](AUTH_SECURITY_AUDIT.md).


## Final production-readiness audit

The latest component-by-component audit is available in [`FINAL_PRODUCTION_READINESS_AUDIT.md`](FINAL_PRODUCTION_READINESS_AUDIT.md). It records the exact evidence, environment-dependent checks, disabled downloader status, and remaining blockers. Vidora must not be labeled fully production-ready until the documented Docker, PostgreSQL/Redis, mobile-device, approved-extractor, reconciliation, and deployment-security checks are completed.

## Final validation status

The latest local backend validation passed with 95 tests, 2 service-gated skips, compileall, Ruff, mypy across 109 files, and pip-audit with no known vulnerabilities. GitHub evidence confirmed the Docker job passed, while the integration, security, and Flutter jobs exposed blockers that are being corrected: an Alembic revision identifier exceeded PostgreSQL's version-column limit, the configured Trivy action tag was invalid, and two Dart files required formatter changes. The repository is not fully production-ready until a corrected GitHub Actions run is green and mobile/device plus approved media-adapter limitations are resolved.

## Final CI completion

GitHub Actions run `31829774202` passed every required backend, PostgreSQL/Redis integration, Flutter, Docker, security, and YAML job. The backend passed 95 tests, compileall, Ruff, mypy across 109 files, and pip-audit. Flutter passed dependency retrieval, code generation, strict formatting, analysis, and tests after CI installed the existing media_kit Linux dependency. The system is still not fully production-ready because approved real media adapters, Android/iOS device validation, release signing, and operational deployment evidence remain incomplete.

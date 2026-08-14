# Vidora Architecture

## Scope

Vidora is a Flutter client and FastAPI backend for authorized media analysis, download lifecycle management, managed files, local playback, and playlists. The system deliberately excludes DRM circumvention, CAPTCHA bypass, paywall bypass, authentication bypass, anti-bot bypass, and unsupported platform extraction.

## Request and persistence flow

```text
Flutter
  ↓ Riverpod controllers and feature views
API routes / WebSocket
  ↓ authentication, validation, rate limiting, request ID
Services
  ↓ business rules and state transitions
Repositories
  ↓ SQLAlchemy 2.x transactions
PostgreSQL
```

Routes do not perform raw SQL, direct filesystem operations, or direct Redis operations. Services own business behavior, repositories own persistence, and dependencies enforce the authenticated user context. Client-supplied `user_id` values are not used for authorization.

## Download flow

```text
Flutter analyzer
  ↓
POST /api/v1/downloads
  ↓ idempotency and ownership validation
Redis Streams
  ↓ consumer group, acknowledgement, retry, pending recovery
Worker
  ↓ state validation and authorized extractor resolution
Authorized Extractor
  ↓ actual progress only; unavailable adapters fail explicitly
Managed Storage
  ↓ canonical path and symlink/traversal protection
Library metadata + PostgreSQL
  ↓
WebSocket lifecycle event to Flutter
```

The worker acknowledges a stream message only after the task outcome is persisted. Transient failures are retried with a bounded policy; permanent failures or exhausted retries enter a terminal failure/dead-letter path. Redis failure never produces a successful queue response.

## Analyzer boundary

Only Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch are in the registry allowlist. Each platform has an isolated extractor package. Analyzer results expose only observed or verified metadata. Unavailable adapters return `supported=false`, `FEATURE_NOT_AVAILABLE`, empty format lists, and null unavailable fields. The analyzer never invents a download URL, size, duration, bitrate, format, or progress value.

Public URL validation rejects invalid schemes, embedded credentials, localhost, loopback, private, reserved, link-local, and cloud metadata destinations. DNS answers are checked before outbound access, and adapters must reuse validated resolution data to reduce DNS-rebinding risk. Network egress restrictions and redirect revalidation remain deployment responsibilities.

## Flutter feature boundaries

```text
lib/
  app.dart
  config/
  core/
    api/
    config/
    downloads/
    models/
    network/
    storage/
    theme/
  features/
    auth/
    analyzer/
    downloads/
    files/
    favorites/
    history/
    home/
    library/
    player/
    playlists/
    settings/
  navigation/
  shared/
```

Views render Riverpod state and trigger controller actions. API access remains in the centralized client/service boundaries. The player uses `media_kit`; Android background work uses WorkManager and iOS uses Background URLSession behind MethodChannel/EventChannel contracts. Native completion is only a signal: backend task state remains authoritative before a download is exposed as completed.

## Runtime and deployment

Production uses PostgreSQL and Redis, with Alembic as the schema authority. API and worker containers run as non-root users with read-only roots, writable managed media and temporary volumes, dropped capabilities, `no-new-privileges`, health checks, and restart policies. Production configuration rejects insecure JWT secrets, SQLite, automatic schema creation, wildcard CORS, and insecure HTTP origins.

The Compose stack mounts the same named `media_data` volume into API and worker. PostgreSQL and Redis are persistent services and should remain private behind network policy, firewall controls, authentication, encrypted backups, and monitored restore procedures.

## Verification boundary

Automated backend and Flutter tests validate application behavior. CI additionally runs Python compilation, Ruff, mypy, Alembic migration checks against PostgreSQL, Flutter formatting/analyze/test, and Docker Compose/image checks. Android and iOS device builds, signing, notification rendering, background scheduling under real OS policy, and production network controls require platform and deployment environments; they must not be represented as verified by sandbox-only tests.

## Current infrastructure verification

The current Compose definition contains API, worker, PostgreSQL, and Redis services. API and worker use the same PostgreSQL database URL pattern and the same Redis service endpoint. Both API and worker mount the named writable `media_data` volume at `/app/data/media`, so production downloads are not stored only in a container layer.

The API is gated on healthy PostgreSQL and Redis services. Its liveness check uses `/health`, while `/ready` performs dependency checks and returns HTTP 503 when PostgreSQL or Redis is unavailable. The worker writes `/tmp/vidora-worker.ready` only after successful dependency checks; its healthcheck validates marker freshness rather than printing a constant success value.

The Compose services use non-root execution, read-only roots for API and worker, tmpfs for temporary writes, dropped capabilities, `no-new-privileges`, persistent PostgreSQL/Redis/media volumes, restart policies, and dependency health conditions. A live Docker Compose build/up/ps verification was not possible in the sandbox because Docker was unavailable. The repository's CI workflow contains Compose configuration and backend image-build checks for a Docker-capable runner.


## Final audit addendum

The final component audit is recorded in [`FINAL_PRODUCTION_READINESS_AUDIT.md`](FINAL_PRODUCTION_READINESS_AUDIT.md). The architecture is modular and substantially hardened, but full production readiness remains blocked by unavailable Docker/runtime validation, unverified Android/iOS device behavior, intentionally disabled approved media download integrations, and the missing trusted mobile-to-backend file reconciliation contract.

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

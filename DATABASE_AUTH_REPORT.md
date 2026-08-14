# Vidora Database and Authentication Report

**Repository:** Existing Vidora repository, continued in place
**Scope:** Production-grade database and authentication layer
**Download engine:** Not implemented or changed in this phase
**Remote Git push:** Not performed

## DATABASE

Production uses PostgreSQL through the existing shared `DATABASE_URL` configuration. Local development continues to support SQLite without creating a second persistence implementation. SQLAlchemy 2.x models and managed sessions are used by the API, worker, repositories, and tests.

The schema now includes `User`, `DownloadTask`, `LibraryItem`, `Favorite`, `HistoryItem`, and `RefreshToken` persistence models. Requested domain models contain `created_at` and `updated_at` timestamp metadata, with `Favorite` and `HistoryItem` maintaining relational activity timestamps. Download and library records have non-null user ownership with foreign keys to `users.id` and `ON DELETE CASCADE`. Favorites and history records have foreign keys to both their user and library item, unique user-item constraints, and supporting indexes.

The database is migration-driven. A new forward Alembic migration, `0002_auth_and_relational_library`, adds account security fields, ownership foreign keys, timestamps, relational favorites/history tables, refresh-token persistence, and compound indexes. No repository contains `CREATE TABLE IF NOT EXISTS` or direct table creation logic.

## AUTH

Registration normalizes email addresses, enforces uniqueness, and hashes passwords using Argon2 through `pwdlib`. Plaintext passwords are never persisted. Registration also creates a one-time, expiring email-verification token hash; delivery is intentionally left behind an email-provider integration boundary.

Login returns a short-lived access JWT and an opaque refresh token. Access tokens include `sub`, `typ`, `iss`, `aud`, `iat`, `exp`, and `ver` claims. Refresh tokens are generated with secure randomness and persisted only as SHA-256 hashes. Refresh operations rotate the token and revoke the previous token, preventing reuse.

The current-user dependency validates the bearer scheme, JWT signature, algorithm, issuer, audience, required claims, expiration, active-account state, and token version. Logout requires an authenticated user, revokes the presented refresh session, and increments the user token version so existing access tokens are invalidated.

Password-reset request and confirmation endpoints are implemented as a foundation. Requests use a non-enumerating response, and reset tokens are stored hashed with an expiration. Confirmation replaces the Argon2 password, clears the reset token, and invalidates existing tokens. Email-verification confirmation similarly consumes a one-time expiring token. Actual email delivery is not faked and remains a future provider integration.

## SECURITY

Production settings reject a missing/default/insecure JWT secret and require configured issuer and audience values. The Compose API and worker receive the same production PostgreSQL URL and the same JWT configuration. JWT tokens are not logged; authentication failures return generic messages.

User isolation is enforced at the repository and service boundaries. Resource routes derive ownership from the authenticated user dependency rather than accepting a client-provided `user_id`. User B cannot list or retrieve User A’s downloads, library records, favorites, or history, and cannot mutate User A’s library item through favorite or view routes.

The implementation deliberately retains existing API aliases, including `/api/v1/auth/me`, `/api/v1/user/me`, `/api/v1/analyze`, and `/api/v1/analyzer/preview`. All new routes are registered with FastAPI and therefore appear in OpenAPI documentation.

## TESTS

| Validation | Result |
|---|---:|
| Full `pytest -q` | **24 passed** |
| Registration and Argon2 hashing | Passed |
| Wrong password | Passed |
| Unauthorized request | Passed |
| Invalid token | Passed |
| Expired access token | Passed |
| Refresh rotation and reuse rejection | Passed |
| Logout invalidation | Passed |
| User isolation for downloads/library/favorites/history | Passed |
| Production default JWT secret rejection | Passed |
| Password-reset non-enumeration | Passed |
| Clean Alembic migration | Passed through `0002_auth_and_relational_library (head)` |
| Python compilation | Passed |

One existing Starlette/httpx deprecation warning remains; it does not fail the suite.

## FILES CHANGED

| File | Change |
|---|---|
| `backend/app/db.py` | Added production relational SQLAlchemy models, timestamps, foreign keys, indexes, refresh-token storage, and session configuration |
| `backend/alembic/versions/0002_auth_and_relational_library.py` | Added forward migration for auth state, ownership constraints, favorites/history, refresh tokens, and indexes |
| `backend/app/core/config.py` | Added JWT issuer/audience/TTL settings and production secret validation |
| `backend/app/schemas/auth.py` | Added refresh, logout, reset, verification, and action response contracts |
| `backend/app/schemas/downloads.py` | Made download ownership mandatory in API responses |
| `backend/app/repositories/users.py` | Added account state, timestamp, password, and token-version persistence behavior |
| `backend/app/repositories/library.py` | Added relational Favorite/HistoryItem persistence and authenticated owner-scoped queries |
| `backend/app/services/auth.py` | Implemented Argon2 auth, JWT validation, refresh rotation, logout, password reset, and email verification foundations |
| `backend/app/main.py` | Added documented auth endpoints while preserving existing aliases |
| `backend/tests/test_auth_security.py` | Added authentication, JWT, refresh, logout, hashing, secret-validation, reset, and isolation tests |
| `backend/.env.example` | Documented JWT configuration and production settings |
| `infrastructure/docker-compose.yml` | Propagated production JWT configuration to API and worker |
| `AUDIT.md` | Synchronized the audit with the completed database/authentication phase |

Previous stabilization files remain intact, including the shared Docker/Alembic setup and foundation report.

## REMAINING

The remaining work is operational and product-specific rather than a missing authentication core. Email verification and password reset need a real email provider, delivery templates, rate limiting, and abuse monitoring. Production deployment should move PostgreSQL credentials and JWT secrets to a proper secret manager, add PostgreSQL/Redis integration tests to CI, and schedule cleanup of expired refresh tokens. Account lockout, login throttling, security audit events, and key rotation policy should be added before public release.

The download engine was intentionally not implemented in this phase, as requested. Flutter analysis/device tests and live Docker/PostgreSQL runtime validation require the corresponding external toolchains, which are unavailable in the current sandbox.

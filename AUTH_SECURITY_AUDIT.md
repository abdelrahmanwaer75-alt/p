# Vidora Authentication and Authorization Security Audit

## Scope

This audit covered authentication lifecycle, JWT validation, refresh-token rotation and revocation, password handling, authorization boundaries, WebSocket isolation, endpoint rate limiting, production configuration, and sensitive logging.

## Authentication lifecycle

Registration hashes passwords with Argon2 through `pwdlib`; plaintext passwords are not stored, returned, or logged. Login verifies the Argon2 hash and rejects invalid credentials with a non-sensitive error. Logout revokes the supplied refresh token and increments the user token version, invalidating active access tokens for that account. Refresh consumes a refresh token once, marks it revoked, and issues a new access/refresh pair. Refresh-token reuse is rejected.

Password-reset and email-verification flows are present as foundations. Reset requests are non-enumerating, reset tokens are stored only as hashes with expiry, successful password reset hashes the new password and increments token version, and verification tokens are also hashed and time-limited. Email delivery remains dependent on a configured provider integration and is not falsely reported as complete.

Session restoration uses the current-user endpoint and rejects expired, malformed, revoked, or otherwise invalid sessions.

## JWT controls

Access tokens use HS256 explicitly and contain required `sub`, `typ`, `iss`, `aud`, `iat`, `exp`, and `ver` claims. Decode validation requires the configured issuer and audience, requires expiration and the other mandatory claims, rejects wrong token type, rejects malformed tokens, and compares the token version with the current user record. Production settings reject insecure/default JWT secrets, missing issuer/audience, SQLite, auto-created schemas, insecure CORS, and local Redis endpoints.

## Authorization and isolation

Protected API routes obtain the authenticated user from the bearer token and pass that user identity to repositories/services. Client-provided user IDs are not trusted. Deterministic tests cover library, favorites, history, downloads, playlists, and file endpoints. Foreign playlist and file operations return not-found behavior rather than disclosing another user’s resource.

The downloads WebSocket requires a bearer token, validates it before accepting the connection, reloads each event’s task, and forwards only events whose task owner matches the authenticated user. Foreign-user events are skipped. Unauthorized WebSocket connections are closed with code `4401`.

## Rate limiting

Rate limiting uses Redis `INCR` and expiry keys so multiple API replicas can share limits. Endpoint-specific buckets now exist for authentication, analyzer operations, download creation, and general API traffic. In development/test, a bounded local fallback keeps isolated environments usable. In production, Redis failure is fail-closed and returns a temporary service-unavailable response rather than silently using process-local limits.

Configured defaults are:

| Bucket | Default per minute |
|---|---:|
| Authentication | 60 |
| Analyzer | 30 |
| Download creation | 20 |
| General API | 120 |

## Sensitive data review

A repository scan found no application logging statements that log access tokens, refresh tokens, passwords, authorization headers, bearer values, credentials, or secrets. Request logging records request ID, user ID, task ID, method, path, and status only. Error responses do not include passwords or token values.

## Test evidence

| Check | Result |
|---|---:|
| Full backend pytest suite | **95 passed, 2 skipped** |
| Python compileall | Passed |
| Sensitive logging scan | No sensitive logging patterns found |
| `git diff --check` | Passed |

The two skipped tests are PostgreSQL/Redis service-container integration tests that require external CI services. The local suite emitted one existing Starlette/httpx deprecation warning; it did not affect correctness.

## Remaining risks and deployment requirements

Production still requires a real secret-store-managed JWT secret, shared Redis, TLS termination, secure cookie/header and reverse-proxy policy as applicable, external email delivery for reset and verification, PostgreSQL/Redis integration execution, backup/restore verification, dependency/image scanning, monitoring, and penetration testing. The implementation does not claim unlimited protection against distributed abuse; production deployments should place the API behind an appropriately configured edge/WAF layer and monitor rate-limit backend health.

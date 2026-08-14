# Vidora Security

## Scope

This document records the security controls implemented in the Vidora backend, worker, storage layer, queue, and Flutter-facing API. It is an operational security baseline for production deployment, not a substitute for deployment-specific threat modeling, dependency review, or penetration testing.

## Implemented controls

| Area | Controls |
|---|---|
| Authentication | Argon2 password hashing; short-lived JWT access tokens; hashed refresh tokens; refresh-token rotation; token revocation and user token-version invalidation; issuer, audience, signature, and expiration validation; current-user dependency on protected routes. |
| Secrets | Production settings reject missing or insecure JWT secrets and insecure production defaults. Docker Compose requires database credentials and `JWT_SECRET` through environment interpolation. Secrets and bearer tokens are not written to logs. |
| Authorization | Resource queries are scoped by the authenticated user. Downloads, library items, favorites, history, playlists, playlist items, and file operations do not trust client-supplied ownership identifiers. |
| API protection | Central middleware supplies request IDs, rate limits, security headers, and consistent JSON errors. HTTP errors include both the current `error` envelope and a backwards-compatible `detail` field. |
| CORS | Origins are configured explicitly rather than using a wildcard. Credentialed requests are supported only for configured origins. |
| SSRF | URL validation restricts analysis to the allowlisted Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch platforms. Localhost, loopback, private, reserved, link-local, metadata, invalid-scheme, and file URLs are rejected. DNS resolution is checked before outbound access to reduce DNS-rebinding risk. |
| Extractors | Unsupported or unavailable adapters return an explicit unsupported result. Metadata and formats are never fabricated, and DRM, CAPTCHA, paywall, authentication, and anti-bot bypasses are not attempted. |
| Filesystem | `StorageService` confines paths to managed per-user roots, rejects traversal and unsafe names, and centralizes save, move, rename, delete, existence, metadata, and available-space operations. |
| Queue and worker | Redis Streams consumer groups, acknowledgement, retries, pending-message recovery, dead-letter handling, bounded retry count, and truthful task transitions prevent silent loss and fake progress. Redis failure does not produce a successful queue response. |
| Containers | API and worker run as UID/GID 10001, use read-only root filesystems with `/tmp` tmpfs, drop all Linux capabilities, enable `no-new-privileges`, use health checks, and have restart policies. PostgreSQL and Redis also drop capabilities and use health checks. |
| Logging | Request logs include request ID, authenticated user ID when available, task ID when present in the route, method, path, and status. Passwords, JWTs, refresh tokens, and credentials are not logged. |

## Production requirements

Before deployment, provide a cryptographically random `JWT_SECRET` of at least 32 characters, unique database credentials, a production PostgreSQL instance, a protected Redis instance, explicit `ALLOWED_ORIGINS`, and `ENVIRONMENT=production`. Run Alembic migrations as part of a controlled deployment process; production uses `AUTO_CREATE_DB=false`.

The API should be deployed behind TLS termination and a trusted reverse proxy. Configure proxy limits, trusted host handling, firewall rules, private networking for PostgreSQL and Redis, encrypted backups, secret rotation, centralized log retention, and alerting according to the hosting environment.

## Remaining risks and limitations

| Risk | Required mitigation |
|---|---|
| Rate limiting is process-local | Use a shared Redis-backed limiter or an API-gateway limiter when running multiple API replicas. Tune limits per route and identity after observing production traffic. |
| SSRF validation is defense-in-depth | Keep outbound egress restricted at the network layer, revalidate resolved destinations immediately before connecting, and monitor extractor dependencies for redirect behavior. |
| User-provided media is untrusted | Keep ffmpeg and media parsers patched, run media processing with least privilege, apply CPU/memory/time limits, and consider an isolated processing sandbox. |
| Local storage is not a backup | Use encrypted, access-controlled backups and define retention and recovery objectives. Validate restore procedures regularly. |
| Background mobile execution varies by OS | Android WorkManager and iOS background URLSession remain subject to platform scheduling, connectivity, battery, and policy limits; the app must expose delayed, failed, and offline states honestly. |
| Dependency and image supply chain | Pin and regularly update Python, Flutter, OS, ffmpeg, PostgreSQL, Redis, and container dependencies. Generate SBOMs and scan images before release. |
| Operational controls are deployment-specific | Perform external penetration testing, TLS/reverse-proxy review, database permission review, Redis exposure review, and incident-response exercises before public launch. |

## Verification

The backend test suite currently passes with **75 tests** after the security and analyzer hardening updates. Python compilation checks also pass. One existing dependency warning remains: Starlette reports that the installed `httpx` integration is deprecated and should be reviewed during dependency maintenance. Ruff and mypy were not available in the sandbox and are enforced by CI instead.

## Mobile release security

Android release signing must use a deployment-injected production keystore. Debug signing is intentionally not configured for release artifacts. Android/iOS builds, signing, notification rendering, and OS background scheduling require platform SDKs, devices, certificates, and deployment credentials; they are not claimed as sandbox-verified.

## Reporting

Do not include passwords, access tokens, refresh tokens, private keys, database credentials, or user media in issue reports. For a suspected vulnerability, preserve the request ID and relevant task ID where available, redact sensitive values, and report through the project's private security process.

## Release checklist

- [ ] Production secrets are injected through a secret manager or protected environment, never committed.
- [ ] `ENVIRONMENT=production` and `AUTO_CREATE_DB=false` are set.
- [ ] `ALLOWED_ORIGINS` contains only approved HTTPS origins.
- [ ] PostgreSQL and Redis are private and authenticated.
- [ ] TLS, reverse-proxy limits, firewall, and egress controls are active.
- [ ] Alembic migrations have been reviewed and applied.
- [ ] Container image and dependency scans are clean or formally accepted.
- [ ] Backups and restore tests are complete.
- [ ] Security-focused tests and the full test suite pass.
- [ ] Monitoring and incident-response contacts are configured.

Last reviewed: 2026-08-14

This file should be updated whenever authentication, extractors, storage, queue, deployment, or dependency controls change.



## Final audit correction

The current validation evidence supersedes the earlier point-in-time count: **95 backend tests pass with 2 external-service skips**, and **15 Flutter tests pass**. Endpoint-specific authentication, analyzer, download-creation, and general API rate-limit buckets are implemented; production rejects local Redis and fails closed when the shared Redis rate-limit backend is unavailable. See [`FINAL_PRODUCTION_READINESS_AUDIT.md`](FINAL_PRODUCTION_READINESS_AUDIT.md) for the complete status table and remaining deployment blockers.

## Final security validation status

The backend security suite and dependency audit pass locally. GitHub security execution is not yet green because the previous workflow referenced an unresolved Trivy Action tag; the final workflow replaces it with a verified release and requires a new successful run. Production defaults remain guarded, and no passwords, tokens, or authorization headers are logged by application code.

## Final CI completion

GitHub Actions run `31829774202` passed Gitleaks and Trivy, as well as the backend security and dependency checks. Production remains subject to deployment-specific TLS, egress, secret-management, backup, monitoring, and penetration-testing controls; these are not inferred from a green repository scan.

# Vidora Full Audit

## Scope

This audit compares the local implementation with the two attached Vidora specifications. The repository is intentionally not pushed during this review.

## Gap matrix

| Area | Specification expectation | Current state | Priority | Planned correction |
|---|---|---|---|---|
| Allowed platforms | Reddit, Vimeo, Dailymotion, SoundCloud, Twitch; no YouTube/Instagram/Facebook | Detector contains prohibited platforms and omits Dailymotion, SoundCloud, and Twitch | Critical | Align platform enum, detector, and policy registry with the allowed list |
| Analyzer | Real metadata and formats through authorized adapters | URL validation and platform detection only; registry contains no configured adapters | Critical | Keep the safe boundary, add explicit adapter interfaces and mark metadata unavailable until an approved adapter is installed |
| Downloads | Queue, real worker, progress, cancellation, output files | Redis queue exists; worker only marks tasks failed because no adapter is configured; no cancellation or output record | Critical | Add task lifecycle fields, cancellation endpoint, output metadata, and a safe adapter hook |
| Database | PostgreSQL, ORM, migrations | SQLite repositories with hand-written schema creation; no migrations or SQLAlchemy | High | Keep SQLite for local development but add migration/version documentation; PostgreSQL production wiring remains incomplete |
| Real-time updates | WebSocket progress channel | Flutter polls every five seconds; no WebSocket endpoint | High | Document polling as local fallback; WebSocket remains a future production phase |
| Flutter architecture | Riverpod, Freezed, GoRouter, Isar, easy_localization, media_kit, file_picker | Monolithic `main.dart`, manual models, direct API calls, no local database, no player, no file picker | High | Refactor incrementally; first centralize API/session models and add explicit feature boundaries |
| Files and player | File browser, offline playback, media_kit, local file metadata | Library API and list UI exist, but no local file storage, player, or file picker | Critical | Add media output contracts and a player boundary; native playback still requires platform integration |
| Playlists | Create/manage playlists and playlist downloads | Not implemented | High | Add playlist schema/repository/API after media output persistence |
| Background mobile downloads | Android WorkManager and iOS Background URLSession | Not implemented | Critical for mobile release | Requires native Android/iOS integration and device-level verification |
| Authentication | JWT, password hashing, account endpoints | Implemented with Argon2 and JWT; mobile secure storage implemented | Medium | Add token restoration, logout state propagation, and refresh/revocation strategy |
| Infrastructure | Docker, Compose, PostgreSQL, Redis, Nginx, CI/CD | Docker/Compose definitions exist; Docker unavailable in sandbox; no Nginx or CI workflow | Medium | Add health checks, production secret validation, and CI configuration |
| API contract | `/analyze`, downloads, files, user, WebSocket | `/analyzer/preview`, downloads, library/favorites/history, auth; no WebSocket/files/user profile contract | High | Add compatibility aliases and explicit API documentation |
| Testing | Unit, integration, widget, security, end-to-end | Backend and Flutter basic tests pass; no real Redis/PostgreSQL/mobile device tests | High | Add contract/security tests; infrastructure tests require external services |

## Corrections applied in this review

The first local correction set will remove prohibited platforms from the supported-platform contract, add the allowed platforms named in the specification, harden the development configuration, and add API compatibility/documentation. No remote Git operation is part of this review.

## Remaining non-local limitations

A genuine production release still requires platform-approved extractor implementations, legal review of each adapter, PostgreSQL migrations, native background download integrations, media playback, CI/CD, and device testing. These cannot be honestly represented as complete until their code and tests exist.

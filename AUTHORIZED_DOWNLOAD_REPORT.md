# Vidora Authorized Download Adapter Report

## Scope

This phase reviewed the real media download path only. The implementation preserves the allowlist of Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch. It does not add YouTube, Instagram, Facebook, TikTok, or X/Twitter, and it does not bypass DRM, CAPTCHA, authentication, paywalls, or anti-bot controls.

## Platform status

| Platform | Status | Exact reason |
|---|---|---|
| Reddit | **DISABLED** | The isolated adapter module exists, but no platform-approved metadata, format, authorization, or download integration is configured. It returns `FEATURE_NOT_AVAILABLE` and empty format lists. |
| Vimeo | **DISABLED** | The isolated adapter module exists, but no approved authorization/API integration is configured. It does not fabricate metadata, formats, URLs, or files. |
| Dailymotion | **DISABLED** | The isolated adapter module exists, but no approved extractor/download integration is configured. It returns an explicit unavailable result. |
| SoundCloud | **DISABLED** | The isolated adapter module exists, but no approved authorization and download path is configured. It does not pretend to support tracks or formats. |
| Twitch | **DISABLED** | The isolated adapter module exists, but no approved authorization/download integration is configured. It remains unavailable rather than bypassing access or anti-bot controls. |

No platform is currently classified as IMPLEMENTED or PARTIALLY IMPLEMENTED for actual downloading. This is intentional: the project has no configured platform-approved integration that can safely and truthfully execute a real download under the stated constraints.

## Architecture controls

Each platform remains isolated under `backend/app/extractors/<platform>/`. The common `PlatformExtractor` contract provides `analyze()`, `get_metadata()`, `get_formats()`, `download()`, `validate()`, and backward-compatible `validate_authorization()` behavior. The registry contains only the five allowed platforms.

Unavailable adapters return `supported=false`, empty `formats`, `audio_formats`, and `video_formats`, null unavailable metadata, and a message containing `FEATURE_NOT_AVAILABLE`. The base download operation raises `DownloadNotAvailable`; it never creates an output file and never emits fabricated progress.

The queue and worker retain Redis Streams acknowledgement, retry, pending recovery, dead-letter, cancellation, idempotency, centralized storage, and backend-authoritative completion behavior. These paths are not marked successful for a platform whose adapter is disabled.

## Verification

The deterministic capability tests cover every allowlisted platform and verify:

- platform isolation and allowlist membership;
- explicit disabled state;
- truthful unavailable analysis results;
- empty format lists when no adapter is configured;
- no fabricated title, duration, estimated size, or progress;
- download refusal through `DownloadNotAvailable`;
- no fake output creation;
- the common validation contract.

Local validation completed with **85 passed, 2 skipped**, Python compilation success, and `git diff --check` success. The skipped tests are the external PostgreSQL/Redis service-container tests that require CI services.

## Enabling a platform later

A platform may be moved from DISABLED to PARTIALLY IMPLEMENTED or IMPLEMENTED only after an approved integration is supplied, authorization requirements are explicit, metadata and formats come from verified responses, downloads use authorized URLs or APIs, redirects and DNS are revalidated, cancellation interrupts the actual transfer, and deterministic tests cover success, transient failure, permanent failure, cancellation, and cleanup.

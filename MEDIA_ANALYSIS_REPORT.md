# Vidora Media Analysis Architecture Report

**Repository:** Existing Vidora repository, continued in place
**Scope:** Safe media analysis and extractor architecture
**Downloading:** Intentionally not implemented
**Remote Git push:** Not performed

## Architecture

The extractor package now contains the requested interface and platform modules:

| File | Responsibility |
|---|---|
| `backend/app/extractors/base.py` | `PlatformExtractor`, metadata contract, authorization gate, unavailable-adapter result, and structured result normalization |
| `backend/app/extractors/registry.py` | Explicit five-platform allowlist, extractor lookup, and policy decisions |
| `backend/app/extractors/reddit.py` | Reddit adapter boundary, unavailable by default |
| `backend/app/extractors/vimeo.py` | Vimeo adapter boundary, unavailable by default |
| `backend/app/extractors/dailymotion.py` | Dailymotion adapter boundary, unavailable by default |
| `backend/app/extractors/soundcloud.py` | SoundCloud adapter boundary, unavailable by default |
| `backend/app/extractors/twitch.py` | Twitch adapter boundary, unavailable by default |

Every adapter exposes `analyze()`, `get_metadata()`, `get_formats()`, and `validate_authorization()` through the shared `PlatformExtractor` contract. No adapter performs network extraction yet. This is deliberate: unavailable adapters return `supported=false`, empty format arrays, no fabricated metadata, and a clear explanation.

## Supported platforms

The registry contains exactly Reddit, Vimeo, Dailymotion, SoundCloud, and Twitch. Generic URLs and prohibited platforms such as YouTube, Instagram, Facebook, TikTok, and X/Twitter are not registered as extractors and return `supported=false` with an explicit allowlist message.

## Analyzer result

`AnalyzerResult` now provides the requested structured fields: platform, supported state, title, description, thumbnail, duration, uploader, formats, audio formats, video formats, estimated size, MIME type, extension, quality, restrictions, and message. Existing compatibility fields (`content_kind`, `creator`, `duration_seconds`, and `thumbnail_url`) remain available for existing clients.

Both `POST /api/v1/analyzer/preview` and the existing `POST /api/v1/analyze` alias route through the registry-backed analyzer service. The preview path is asynchronous and does not pretend that a platform adapter exists when it does not.

## Security

The analyzer accepts only HTTP and HTTPS URLs, rejects embedded credentials, localhost names, `.local`, `.localhost`, and `.internal` hostnames, metadata service hostnames, private IPs, loopback addresses, link-local addresses, multicast, unspecified addresses, reserved addresses, and non-global DNS answers.

DNS validation resolves all returned addresses and rejects the hostname if any answer is unsafe. The validation function documents the required future adapter behavior: approved adapters must reuse the validated resolution result when opening their connection rather than resolving the hostname again. This prevents a DNS answer from changing between validation and the outbound connection. No current adapter performs outbound extraction.

The authorization gate rejects unauthenticated adapter execution with an explicit `PermissionError`. DRM, CAPTCHA, paywall, authentication, and anti-bot bypass behavior was not added.

## Tests

| Test area | Result |
|---|---:|
| Full backend suite | **43 passed** |
| Five allowed platforms detected | Passed |
| Missing adapters return empty formats and no metadata | Passed |
| Prohibited platform rejection | Passed |
| Invalid scheme rejection | Passed |
| Localhost/private IP rejection | Passed |
| Metadata endpoint rejection | Passed |
| DNS-rebinding unsafe answer rejection | Passed |
| Authorization gate | Passed |
| Python compilation | Passed |

One existing Starlette/httpx deprecation warning remains and does not fail the suite.

## Remaining

The next phase may add an approved platform adapter only after legal/platform authorization, with network access constrained by the validated DNS/address policy. Such an adapter must return verified metadata and formats, must not bypass access controls, and must include adapter-specific tests. Actual media downloading, queue execution changes, DRM handling, CAPTCHA handling, paywall handling, authentication bypass, and anti-bot bypass remain intentionally out of scope.

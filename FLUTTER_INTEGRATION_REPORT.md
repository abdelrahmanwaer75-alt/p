# Vidora Flutter Integration Report

**Repository:** Existing Vidora repository, continued in place
**Scope:** Flutter-to-backend integration
**Remote Git push:** Not performed

## ARCHITECTURE

The Flutter application now has an incremental architecture under `lib/core`, `lib/features`, `lib/routing`, and `lib/shared`. The existing backend-facing UI behavior was not extended with widget-level network calls. Active screens use Riverpod controllers for authentication, analysis, downloads, library, favorites, history, and settings.

| Layer | Implementation |
|---|---|
| Core configuration | `API_BASE_URL` compile-time configuration with `http`→`ws` and `https`→`wss` conversion |
| Core transport | Typed Dio client with REST methods, bearer token attachment, and mapped failure categories |
| Secure storage | Access token, refresh token, and account email persisted through `flutter_secure_storage` |
| Models | Immutable source models with Freezed annotations and explicit JSON serialization contracts |
| State | Riverpod `StateNotifierProvider` controllers and shared resource states |
| Routing | GoRouter splash, onboarding, auth, forgot-password, and protected feature routes |
| Features | auth, home, analyzer, downloads, library, favorites, history, and settings route modules |
| Shared UI state | Loading, success, empty, error, unauthorized, and offline are distinct states |

## SESSION RESTORATION

At startup, the auth controller restores the access and refresh tokens from secure storage. When an access token exists, it calls `/api/v1/user/me` and only enters the authenticated state after the backend validates the token. Missing, expired, invalid, or unavailable-storage cases fail closed to the unauthenticated state and clear the persisted session. Protected routes redirect to `/login`, while authenticated users are redirected away from splash and auth pages to `/home`.

Login and registration save the returned access and refresh tokens. Logout calls the backend logout endpoint when possible and always clears secure storage locally. The refresh endpoint is implemented in the typed client for future token-refresh interception and explicit account-session flows.

## API BASE URL

The hardcoded `127.0.0.1:8000` default was removed from both the active and compatibility clients. The application now uses:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

The default is Android-emulator friendly. iOS simulator, physical-device, and production deployments can supply their reachable host or HTTPS endpoint through the same compile-time define. WebSocket URLs are derived automatically, using `ws` for HTTP and `wss` for HTTPS.

## WEBSOCKET DOWNLOAD EVENTS

The backend now exposes authenticated `GET /api/v1/ws/downloads` WebSocket handling at `/api/v1/ws/downloads`. It validates the bearer token with the same issuer, audience, expiration, and token-version checks used by REST APIs, then filters Redis event-stream messages by the authenticated task owner.

The Flutter downloads controller connects to the endpoint and immediately applies task events to Riverpod state. Supported event names are `download.created`, `download.started`, `download.progress`, `download.completed`, `download.failed`, and `download.cancelled`. If the WebSocket cannot connect or closes, the controller starts a five-second REST polling fallback. Polling never replaces the explicit error state: an HTTP 500 becomes `error`, a 401 becomes `unauthorized`, and a connection failure becomes `offline`; it is not displayed as an empty list.

## TESTS AND VALIDATION

| Check | Result |
|---|---:|
| Backend syntax compilation after WebSocket integration | Passed |
| Backend regression suite | **50 passed** |
| Flutter hardcoded loopback URL scan | Passed |
| `git diff --check` | Passed |
| Flutter provider test files added | Session restoration, expired-session clearing, API URL configuration |
| `flutter analyze` | Not run: Flutter/Dart executables are unavailable in the current sandbox |
| `flutter test` | Not run: Flutter/Dart executables are unavailable in the current sandbox |

The Flutter test files are included in the repository and should be run in a Flutter-enabled development or CI environment with `flutter pub get`, `dart run build_runner build --delete-conflicting-outputs`, `flutter analyze`, and `flutter test`.

## FILES CHANGED OR ADDED

| File | Purpose |
|---|---|
| `pubspec.yaml` | Added Riverpod, GoRouter, WebSocket, Freezed, JSON serialization, and build-runner dependencies |
| `lib/main.dart` | ProviderScope and MaterialApp.router entry point with Material 3 settings |
| `lib/core/config/app_config.dart` | `API_BASE_URL` and WebSocket URL derivation |
| `lib/core/storage/session_storage.dart` | Secure access/refresh-token persistence |
| `lib/core/network/api_client.dart` | Typed REST client and failure mapping |
| `lib/core/models/models.dart` | User, AuthSession, AnalyzerResult, MediaFormat, DownloadTask, LibraryItem, Favorite, and HistoryItem models |
| `lib/core/models/models.freezed.dart` | Freezed generated-part placeholder for environments without build_runner |
| `lib/core/models/models.g.dart` | JSON generated-part placeholder for environments without build_runner |
| `lib/shared/state/resource_state.dart` | Explicit resource-state contract |
| `lib/features/auth/auth_providers.dart` | Session restoration and authentication provider |
| `lib/features/providers.dart` | Analyzer, download, collection, WebSocket, polling, and settings providers |
| `lib/routing/app_router.dart` | GoRouter route tree and auth guards |
| `lib/features/auth/auth_pages.dart` | Splash, onboarding, login, register, and forgot-password pages |
| `lib/features/home/home_page.dart` | Provider-compatible home route |
| `lib/features/analyzer/analyzer_page.dart` | Analysis and format-selection screen |
| `lib/features/downloads/downloads_page.dart` | Download state screen with cancellation and explicit errors |
| `lib/features/library/library_page.dart` | Library collection screen |
| `lib/features/favorites/favorites_page.dart` | Favorites collection screen |
| `lib/features/history/history_page.dart` | History collection screen |
| `lib/features/settings/settings_page.dart` | Settings and logout screen |
| `test/providers/session_restoration_test.dart` | Session and configuration tests |
| `test/widget_test.dart` | Updated startup/onboarding routing test |
| `backend/app/services/auth.py` | Shared token-to-user helper for WebSocket authentication |
| `backend/app/queue.py` | Flutter-facing event name normalization |
| `backend/app/main.py` | Authenticated download WebSocket endpoint |

## REMAINING

The next required environment step is to run the Flutter toolchain in CI or on a developer machine. Because code generation dependencies are included, generated Freezed/json_serializable files should be regenerated there rather than relying on the checked-in source-compatible placeholders. Runtime integration tests should also exercise a real PostgreSQL/Redis backend and an authenticated WebSocket client. Actual platform downloading remains intentionally unavailable until an approved extractor implements its download contract.

# Vidora Background Download Report

**Repository:** Existing Vidora repository, continued in place  
**Scope:** truthful Android and iOS mobile background download infrastructure, Flutter bridge, lifecycle events, notifications, and validation  
**Download engine policy:** no fake execution or simulated progress

## ARCHITECTURE

Flutter now exposes a `BackgroundDownloadService` abstraction over a `MethodChannel` named `vidora/background_downloads` and an `EventChannel` named `vidora/background_download_events`. The abstraction supports `start`, `pause`, `resume`, and `cancel`. Native lifecycle events are normalized into `download.created`, `download.started`, `download.progress`, `download.completed`, `download.failed`, `download.paused`, `download.cancelled`, and `download.notification_tap` events.

`BackgroundDownloadService` is a singleton with a broadcast stream, allowing the Downloads Riverpod controller and app-level notification-tap routing to observe the same native event source. The existing backend WebSocket and polling fallback remain active; native events supplement them when the mobile platform owns the transfer.

## ANDROID

Android uses WorkManager with `NetworkType.CONNECTED`, unique work names per task, exponential WorkManager backoff, a foreground notification, and a real `HttpURLConnection` byte stream. The worker writes into the app-managed `Vidora` download directory, reports actual bytes read, uses the response content length when available, and emits completion only after the output file is closed successfully.

The worker honors process cancellation and a persisted pause flag. Android notification actions are represented by a `PendingIntent` targeting `MainActivity` with the task ID. Notification taps are forwarded to Flutter and route the user to the downloads screen. Notification permission, internet, foreground-service, and data-sync permissions are declared in the Android manifest.

The implementation does not claim that WorkManager keeps an arbitrary transfer running without system constraints. WorkManager may defer execution for network, battery, quota, or OS policy reasons. A transfer is considered accepted only when WorkManager enqueue succeeds; no UI progress is fabricated before native progress events exist.

## IOS

iOS uses a background `URLSessionConfiguration` with `sessionSendsLaunchEvents = true` and `URLSessionDownloadDelegate`. Downloads run as URLSession download tasks, report actual byte totals when provided by the server, and move completed files into the app’s `Documents/Vidora` directory after the system delivers the temporary download location.

Pause uses URLSession resume data and resume creates a new download task from the saved resume data. Cancellation uses the actual tracked URLSession task. Background session completion is handed back to the system through `application(_:handleEventsForBackgroundURLSession:completionHandler:)`. Local notifications are requested and emitted for started, progress, completed, failed, paused, and cancelled states. Notification taps carry the task ID back to Flutter.

The implementation respects Apple background execution limits. iOS may suspend, defer, terminate, or otherwise schedule work according to URLSession and system policy. The app does not claim unlimited background execution, immediate progress delivery while terminated, or unrestricted execution after force-quit.

## FLUTTER INTEGRATION

`DownloadsController` subscribes to the native background stream and maps events into the existing Riverpod download state. Progress, byte counts, output paths, errors, and terminal states update only from real native event payloads or the existing backend event/polling paths. Notification taps are observed at the application level and route to `/downloads` for the related task context.

## TESTS AND VALIDATION

| Check | Result |
|---|---:|
| Backend Python compilation | Passed |
| Existing backend regression suite | **57 passed** |
| Native event parser tests added | Added for progress and notification tap payloads |
| Git whitespace validation | Passed |
| Flutter/Dart analyzer and test execution | Not available: `flutter` and `dart` executables are absent in this sandbox |
| Android Gradle native compilation | Attempted; blocked because Android SDK is unavailable in this sandbox |
| iOS native compilation | Not available on this Linux sandbox; requires macOS/Xcode |

The backend test output retains the pre-existing Starlette/httpx deprecation warning only; it does not fail the suite.

## FILES CHANGED

| File | Purpose |
|---|---|
| `android/app/build.gradle.kts` | WorkManager dependency |
| `android/app/src/main/AndroidManifest.xml` | Network, foreground-service, and notification permissions |
| `android/app/src/main/kotlin/com/vidora/vidora/BackgroundDownloadWorker.kt` | Real WorkManager stream transfer, progress, files, and notifications |
| `android/app/src/main/kotlin/com/vidora/vidora/BackgroundDownloadBridge.kt` | MethodChannel operations and event bridge |
| `android/app/src/main/kotlin/com/vidora/vidora/MainActivity.kt` | Flutter channels and notification-tap intent handling |
| `ios/Runner/BackgroundDownloadService.swift` | Background URLSession transfer, resume data, files, notifications, and events |
| `ios/Runner/AppDelegate.swift` | iOS Flutter channels, notification permission, and background URLSession completion |
| `ios/Runner/Info.plist` | iOS background modes |
| `lib/core/downloads/background_download_service.dart` | Flutter MethodChannel/EventChannel abstraction and typed event stream |
| `lib/features/providers.dart` | Riverpod download-state updates from native events |
| `lib/main.dart` | Notification-tap routing integration |
| `test/downloads/background_download_service_test.dart` | Native event parsing tests |

## REMAINING PRODUCTION STEPS

The native transfer currently downloads a URL supplied by the mobile layer. Production integration must call it only for a backend-approved download task and must reconcile native completion with the authenticated backend task/library APIs before presenting the item as completed. The backend remains the authority for authorization, task ownership, extractor policy, and library synchronization.

Before release, run `flutter pub get`, code generation where applicable, `flutter analyze`, and `flutter test` on a Flutter-enabled machine. Run Android Gradle builds and instrumentation tests with a configured Android SDK, and run iOS builds and URLSession lifecycle tests on macOS/Xcode devices or simulators. Verify notification permission flows, network transitions, process termination, OS rescheduling, force-quit behavior, background-session relaunch, and authenticated file/player opening on real devices.

# Vidora Mobile Background Download Integration Audit

## Scope

This phase audited and hardened the existing Android WorkManager and iOS Background URLSession integrations without placing native code in Flutter widgets or claiming device-level success that was not available in the sandbox.

## Android

Android uses a `MethodChannel` and `EventChannel` bridge, WorkManager `CoroutineWorker`, a foreground notification for active transfers, `NetworkType.CONNECTED` constraints, exponential WorkManager backoff, safe filename sanitization, app-specific managed storage under the Vidora downloads directory, and notification intents that carry only the task ID.

The bridge now uses `ExistingWorkPolicy.KEEP` to avoid replacing an active task when the same task ID is submitted again. Events are buffered while Flutter’s event sink is detached, including notification-tap events generated during app launch or relaunch. The worker reports started, progress, paused, cancelled, failed, and completed signals and keeps network errors separate from cancellation.

## iOS

iOS uses `URLSessionConfiguration.background` with launch events, connectivity waiting, non-discretionary transfer behavior, cellular access, background-session completion callbacks, notification delegation, and app-specific `Documents/Vidora` storage. Existing URLSession tasks are restored from their task descriptions after app relaunch. Pending EventChannel events are buffered until Flutter attaches.

Pause/resume uses URLSession resume data. Completion records managed output path, byte size, and a SHA-256 checksum in the native event signal. The checksum is evidence for a future trusted reconciliation endpoint; it does not mark the backend task completed by itself.

## Flutter bridge and backend authority

Flutter continues to communicate through `MethodChannel('vidora/background_downloads')` and `EventChannel('vidora/background_download_events')`. Native event names are normalized to the `download.*` contract, and checksum metadata is parsed.

Native `completed`, `failed`, and `cancelled` events are treated only as signals. The Flutter download controller reloads the task from the backend for all terminal native events. Notification taps call the authenticated backend open operation before refreshing local state. Native output paths are never used to mark a backend task complete locally.

The existing backend worker remains the authoritative path for server-side task ownership, output validation, library synchronization, and completion. A full trusted mobile-to-backend completion handshake that can verify task ID, authenticated user, uploaded/accessible file, byte size, checksum, and final status still requires a backend reconciliation endpoint and a deployment-specific file-transfer contract. Until that exists, the mobile bridge must not be presented as a replacement for the backend worker.

## Storage and security

Android uses app-specific external files storage and iOS uses the app’s Documents/Vidora directory. Filenames are sanitized and path components are not accepted from user input. The native code does not expose arbitrary filesystem paths through the Flutter API. The backend storage abstraction remains separate and authoritative for server-managed media.

## Validation

| Check | Result |
|---|---:|
| Flutter formatting | Passed |
| Flutter analyzer | Passed before native-only changes; rerun required after final bridge contract changes |
| Flutter unit/widget tests | Existing suite available; native event contract tests extended |
| Android WorkManager/device lifecycle | **NOT VERIFIED ON REAL DEVICE** |
| iOS Background URLSession/device lifecycle | **NOT VERIFIED ON REAL DEVICE** |
| App-killed/relaunch delivery | Static implementation reviewed; **NOT VERIFIED ON REAL DEVICE** |
| Network reconnect and OS scheduling | **NOT VERIFIED ON REAL DEVICE** |
| Notification rendering/tap on Android and iOS | **NOT VERIFIED ON REAL DEVICE** |
| Native build/signing | Requires Android/iOS platform runners and signing credentials |

## Remaining work before claiming end-to-end mobile completion

A device/CI validation matrix is still required for foreground, background, killed, reconnect, completion, failure, cancellation, pause/resume, notification tap, and relaunch. The backend also needs a trusted mobile reconciliation contract before a native local completion can create or finalize server-side library metadata. No unlimited background execution is claimed for either platform.

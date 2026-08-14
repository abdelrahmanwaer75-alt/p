# Vidora Download Manager and File Manager Report

**Repository:** Existing Vidora repository, continued in place
**Scope:** Download Manager, centralized storage, local File Manager, and library synchronization
**Remote Git push:** Not performed

## DOWNLOAD MANAGER

The Flutter download screen now groups tasks into **Active**, **Queued**, **Completed**, **Failed**, and **Cancelled** sections. Each task displays its verified title, thumbnail indicator when available, current status, real progress when supplied by the worker, speed, ETA, downloaded bytes, total bytes, and error message when present.

Progress remains truthful. The UI renders a percentage only when the backend has a real `progress_percent` value. Unknown progress is displayed as unavailable rather than estimated. WebSocket events from the worker update Riverpod state immediately, while REST polling remains a fallback if the WebSocket is unavailable.

Actions are state-gated in the Flutter UI and enforced again by the backend service:

| State | Valid actions |
|---|---|
| `queued` | Pause, Cancel |
| `starting` / `downloading` | Pause, Cancel |
| `paused` | Resume, Cancel |
| `completed` | Open, Delete |
| `failed` | Retry, Delete |
| `cancelled` | Delete |

The backend now exposes pause, resume, retry, open, and delete endpoints in addition to the existing cancel endpoint. Active tasks cannot be deleted, completed tasks cannot be cancelled, only paused tasks can resume, and only failed tasks below the retry limit can retry. Ownership remains authenticated-user scoped.

## STORAGE SERVICE

`backend/app/services/storage.py` centralizes managed filesystem access. It provides `save`, `delete`, `move`, `rename`, `exists`, `metadata`, `available_space`, and relative-path conversion. All resolved paths must remain inside the Vidora-managed media root.

The service rejects unsafe filenames, path separators in filenames, `.` and `..`, traversal segments, and destinations outside the managed root. Public file responses expose safe relative paths rather than arbitrary absolute filesystem locations. Missing files are not fabricated into file-manager records; the file listing skips library rows whose managed file is absent.

## FILE MANAGER

The backend now supports authenticated file listing with search, safe sort modes (`name`, `size`, `date`, `type`), and ascending/descending order. File records include the library ID, relative path, filename, size, MIME type, extension, media type, duration, modification date, favorite state, and title.

The following owner-scoped actions are implemented:

`GET /api/v1/files` supports search and sorting. `GET /api/v1/files/{id}` returns verified metadata and available storage space. `POST /api/v1/files/{id}/rename` renames a managed file safely. `POST /api/v1/files/{id}/move` moves it to a managed folder. `DELETE /api/v1/files/{id}` removes the physical file and library record. `POST /api/v1/files/{id}/open` verifies a file for client opening. `POST /api/v1/files/{id}/share` verifies and returns managed metadata for a client-side sharing action. Favorites remain owner-scoped through the existing library favorite endpoint.

The Flutter Library route is now a File Manager view with search, sort selection, metadata display, and rename, move, delete, open, share, and favorite actions routed through `FileManagerController`. Widgets do not call the API client directly.

## LIBRARY SYNCHRONIZATION

When a worker receives a real extractor result, it persists the completed task and creates a `LibraryItem` containing the output path, filename, media type, MIME type, verified byte size, source URL, title, and downloaded timestamp. The library schema migration `0004_library_file_metadata` adds `filename`, `mime_type`, `file_size`, `duration`, `thumbnail`, and `downloaded_at` columns.

No library item is created from simulated progress or an unavailable extractor. If an approved download adapter is not implemented, the task remains truthful and fails with `FEATURE_NOT_AVAILABLE` as established in the previous phase.

## SECURITY

All file-manager operations use the authenticated user ID and reject cross-user lookups. Storage operations resolve and validate every path against the managed root. Rename validates the complete filename, while move validates the destination before checking the source. This ensures path traversal attempts are rejected consistently rather than being treated as ordinary missing-file requests.

## TESTS AND VALIDATION

| Check | Result |
|---|---:|
| Full backend `pytest -q` | **55 passed** |
| Download state action coverage | Passed for pause, resume, retry, cancel, open, and delete service rules |
| Storage save/metadata | Passed with a real file |
| Storage rename/move/delete | Passed |
| Path traversal and absolute escape rejection | Passed |
| Missing storage errors | Passed |
| File-manager API metadata | Passed |
| File-manager rename/move/delete | Passed with real managed files |
| File-manager search/sort contract | Implemented and covered through route/service integration |
| Library synchronization | Passed for filename, MIME type, and byte size |
| File-manager user isolation | Passed |
| Alembic migration | Passed through `0004_library_file_metadata (head)` |
| Required schema verification | Passed for task lifecycle and library file metadata columns |
| Python compilation | Passed |
| `git diff --check` | Passed |
| Flutter analyzer/tests | Not run because Flutter/Dart executables are unavailable in the current sandbox |

One existing Starlette/httpx deprecation warning remains and does not fail the backend suite.

## FILES CHANGED

| File | Purpose |
|---|---|
| `backend/app/services/storage.py` | Centralized secure filesystem service |
| `backend/app/services/files.py` | Owner-scoped file-manager service |
| `backend/app/schemas/files.py` | File listing, metadata, and action contracts |
| `backend/app/schemas/library.py` | Durable library file metadata fields |
| `backend/app/db.py` | Library file metadata model columns |
| `backend/alembic/versions/0004_library_file_metadata.py` | Library metadata migration |
| `backend/app/repositories/library.py` | File search/sort, lookup, update, and delete persistence |
| `backend/app/repositories/downloads.py` | Download task deletion persistence |
| `backend/app/services/downloads.py` | State-valid pause/resume/retry/open/delete operations |
| `backend/app/main.py` | Download action and file-manager API routes |
| `backend/worker.py` | Completion-to-library metadata synchronization |
| `backend/app/core/models/models.dart` | Flutter model additions for download and library metadata |
| `lib/core/models/models.dart` | Flutter DownloadTask, LibraryItem, and ManagedFile models |
| `lib/core/network/api_client.dart` | Flutter download and file-manager API methods |
| `lib/features/providers.dart` | Download actions and FileManagerController |
| `lib/features/downloads/downloads_page.dart` | Sectioned Download Manager UI |
| `lib/features/library/library_page.dart` | Searchable File Manager UI |
| `backend/tests/test_storage.py` | Storage security and operation tests |
| `backend/tests/test_file_manager.py` | File-manager API and isolation tests |
| `backend/tests/test_download_lifecycle.py` | Library metadata synchronization assertions |

## REMAINING

Actual platform downloading remains intentionally deferred until an approved extractor implements the download contract. The `open` and `share` backend actions currently verify and return managed metadata; native client launching and platform share sheets should be connected in a Flutter-enabled environment using a platform-safe package. Flutter dependency generation, `flutter analyze`, and `flutter test` must also be run in CI or on a machine with the Flutter SDK. Production should add PostgreSQL/Redis integration tests for file lifecycle operations, file-serving authorization if remote access is required, disk-quota monitoring, and cleanup reconciliation for database rows whose files are removed externally.

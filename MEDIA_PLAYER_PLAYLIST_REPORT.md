# Vidora Media Player and Playlist Report

**Repository:** Existing Vidora repository, continued in place  
**Scope:** media_kit player state, local-file playback boundary, playlists, playlist items, API isolation, and tests  
**Remote Git push:** Not performed in this phase

## DATABASE

The database now includes `playlists` and `playlist_items` through Alembic migration `0005_playlists`. Each playlist belongs to one authenticated user through `playlists.user_id` with `ON DELETE CASCADE`. Each playlist item belongs to a playlist and a library item. Deleting a user, playlist, or library item cascades only to the dependent playlist records; playlist ownership is never inferred from client-supplied IDs.

Playlist item ordering is stored as an integer `position` with indexes on playlist, library item, and playlist/position. A corrective migration `0006_remove_legacy_download_owner` also removes the obsolete download `owner_id` column after the existing data has been backfilled to `user_id`, keeping the database model and repository contract aligned.

## API

The authenticated API now exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/playlists` | List only the current user’s playlists |
| `POST /api/v1/playlists` | Create a playlist |
| `GET /api/v1/playlists/{id}` | Read a playlist and ordered items |
| `PATCH /api/v1/playlists/{id}` | Rename or update description |
| `DELETE /api/v1/playlists/{id}` | Delete a playlist and cascade its items |
| `POST /api/v1/playlists/{id}/items` | Add an owner-owned library item |
| `DELETE /api/v1/playlists/{id}/items/{item_id}` | Remove an item and compact positions |
| `POST /api/v1/playlists/{id}/reorder` | Replace the complete ordered item list |
| `POST /api/v1/playlists/{id}/play` | Validate and return the owner’s playlist for playback |
| `POST /api/v1/playlists/{id}/download` | Explicitly reports `FEATURE_NOT_AVAILABLE` until approved extractor-backed playlist downloading exists |

The repository performs every playlist and item lookup with the authenticated user ID. A user cannot read, modify, reorder, delete, or add items to another user’s playlist. A library item from another account is rejected even if its UUID is known.

## MEDIA PLAYER

Flutter now includes `media_kit`, `media_kit_video`, and `media_kit_libs_video`. `MediaKit.ensureInitialized()` runs before the application starts. `PlayerController` is a Riverpod `StateNotifier` that tracks the current item, playback state, position, duration, volume, speed, playlist, current index, and error state.

The player supports local media opening through `Player.open(Media(path))`, video rendering through `media_kit_video`, and audio playback through the same media_kit player without a video surface. Controls include play, pause, seek, forward ten seconds, backward ten seconds, volume, speed selection, next, previous, and playlist playback. An empty playlist or missing local path fails explicitly; no fake playable source or simulated state is created.

The `/player` route is authenticated. The Flutter player screen presents the current item, video or audio surface, real position and duration, progress seeking, playback controls, volume, speed, and errors.

## PLAYLIST UI

The authenticated Flutter route tree now includes `/playlists`, `/playlists/:playlistId`, and `/player`. The Home screen has a Playlists entry point. The Playlists screen supports creation, rename, deletion, item count, and navigation to details. Playlist details support play, add from the current library, remove, and drag-and-drop reorder. Playlist operations are performed through `PlaylistController`; widgets do not call the API client directly.

## TESTS AND VALIDATION

| Check | Result |
|---|---:|
| Alembic upgrade | Passed through `0006_remove_legacy_download_owner (head)` |
| Existing backend regression suite | Passed |
| Playlist CRUD | Passed |
| Playlist item add/remove | Passed |
| Playlist reorder validation | Passed |
| Playlist user isolation | Passed |
| Playlist download feature gate | Passed with HTTP 501 / `FEATURE_NOT_AVAILABLE` |
| Backend total | **57 passed** |
| Python compilation | Passed |
| `git diff --check` | Passed |
| Flutter player test file added | Empty-state, invalid local path, initial-state coverage |
| `flutter analyze` | Not run: Flutter/Dart executables are unavailable in this sandbox |
| `flutter test` | Not run: Flutter/Dart executables are unavailable in this sandbox |

The only backend warning is the existing Starlette/httpx deprecation warning; it does not fail the suite.

## FILES CHANGED

| File | Purpose |
|---|---|
| `backend/app/db.py` | Playlist and playlist-item SQLAlchemy models |
| `backend/alembic/versions/0005_playlists.py` | Playlist schema migration |
| `backend/alembic/versions/0006_remove_legacy_download_owner.py` | Legacy ownership-column cleanup migration |
| `backend/app/schemas/playlists.py` | Playlist API contracts |
| `backend/app/repositories/playlists.py` | User-isolated CRUD, item management, and reorder persistence |
| `backend/app/main.py` | Playlist REST API routes |
| `backend/tests/test_playlists.py` | CRUD, item, reorder, isolation, and feature-gate tests |
| `pubspec.yaml` | media_kit dependencies |
| `lib/main.dart` | media_kit initialization |
| `lib/core/models/models.dart` | Playlist and playlist-item models |
| `lib/core/network/api_client.dart` | Playlist API methods |
| `lib/features/player/player_provider.dart` | Riverpod media-player state and controls |
| `lib/features/player/player_page.dart` | Video/audio player UI |
| `lib/features/playlists/playlist_provider.dart` | Playlist Riverpod controller |
| `lib/features/playlists/playlists_page.dart` | Playlist list and details UI |
| `lib/routing/app_router.dart` | Protected playlist/player routes |
| `lib/features/home/home_page.dart` | Playlist navigation entry point |
| `test/player/player_state_test.dart` | Player state and invalid-file tests |

## REMAINING

The player’s local-file boundary is implemented, but a mobile device can open only paths that exist on that device. Backend media paths are server-managed paths and should not be passed directly to a physical device without a secure authenticated file-transfer/download-to-app-storage step. Native share/open integration can be added with platform plugins after that transfer contract is defined.

Playlist downloading intentionally remains unavailable until the approved extractor implementations can create real download tasks. The API returns an explicit feature-unavailable response rather than pretending that a playlist download was queued. Flutter code generation and media_kit runtime validation must be run in a Flutter-enabled CI or development environment using `flutter pub get`, `dart run build_runner build --delete-conflicting-outputs`, `flutter analyze`, and `flutter test`.

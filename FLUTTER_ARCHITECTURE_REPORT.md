# Vidora Flutter Architecture and UI Report

## Scope

This phase audited the existing Vidora Flutter application and used the supplied [Markti_nti repository](https://github.com/youssef-hossam/Markti_nti) only as a high-level organization reference. No Markti code, business logic, or UI implementation was copied. Vidora remains its own media-management application.

## Verified structure

Vidora keeps a minimal `lib/main.dart` entrypoint and an `app.dart` application root. The application is organized around `config/`, `core/`, `navigation/`, `shared/`, and feature directories for authentication, onboarding, home, analyzer, downloads, library, files, favorites, history, playlists, player, and settings.

Feature controllers/providers remain separate from views and widgets. Existing API calls stay outside widgets and continue to use the shared network client. New feature-specific API facades were added under `lib/core/api/` for `AuthApi`, `AnalyzerApi`, `DownloadsApi`, `FilesApi`, `LibraryApi`, `FavoritesApi`, `HistoryApi`, and `PlaylistsApi`. These facades delegate to the existing `ApiClient`, so the network behavior and authentication flow are not rewritten.

## State and route behavior

Riverpod remains the application state-management boundary. The existing GoRouter guard continues to protect authenticated shell routes and preserve splash, onboarding, login, register, forgot-password, home, analyzer, downloads, library, favorites, history, playlists, player, and settings routes.

The existing shared resource state vocabulary distinguishes loading, success, empty, error, unauthorized, and offline states. The files screen was tightened so error, unauthorized, and offline responses do not fall through to a misleading empty state.

## Localization and directionality

A lightweight `AppLocalizations` delegate now provides English and Arabic shared strings for navigation, home, settings, files, and common status labels. `MaterialApp` declares both supported locales and uses Flutter’s global Material, Widgets, and Cupertino localization delegates. Arabic therefore receives proper RTL directionality instead of only changing a locale value without translated platform strings.

The home, settings, navigation, and files surfaces now consume the shared localization layer. Additional feature-specific copy remains a follow-up area because the existing application contains many screen-specific labels that should be migrated incrementally rather than replaced mechanically.

## Theme and responsive defaults

The shared Material 3 theme now defines consistent light/dark color schemes, typography, adaptive visual density, input fields, cards, dialogs, filled and outlined buttons, and floating snackbars. Existing feature screens inherit these defaults without duplicating styling in widgets.

The current screens use scrollable layouts and adaptive Material controls. Full device-matrix verification on small Android phones, large phones, iPhones, and tablets still requires platform runners or device/simulator coverage.

## Validation

The final local Flutter checks passed:

| Check | Result |
|---|---:|
| `flutter pub get` | Passed |
| `dart format lib test` | Passed |
| `flutter analyze` | No issues found |
| `flutter test` | **15 tests passed** |
| `git diff --check` | Passed |

The test run emitted non-failing PipeWire warnings from the sandbox media environment. They did not affect test results.

## Remaining architecture work

The API facades currently delegate to the established `ApiClient`; they do not yet replace every controller dependency on that client. Full migration can be performed feature by feature without changing endpoint behavior. Screen-specific localization for analyzer, downloads, auth, playlists, player, library, favorites, and history should also continue incrementally. Production visual verification still needs Android/iOS/tablet runners and accessibility review.

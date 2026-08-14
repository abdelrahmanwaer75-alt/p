import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/localization/app_localizations.dart';
import '../features/auth/auth_providers.dart';
import 'auth_guard.dart';
import 'route_names.dart';
import '../features/auth/auth_pages.dart';
import '../features/home/home_page.dart';
import '../features/analyzer/analyzer_page.dart';
import '../features/downloads/downloads_page.dart';
import '../features/library/library_page.dart';
import '../features/favorites/favorites_page.dart';
import '../features/history/history_page.dart';
import '../features/playlists/playlists_page.dart';
import '../features/playlists/playlist_details_page.dart';
import '../features/player/player_page.dart';
import '../features/settings/settings_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final refresh = _RouterRefresh(ref.read(authProvider.notifier).stream);
  ref.onDispose(refresh.dispose);
  return GoRouter(
    initialLocation: RouteNames.splash,
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final location = state.matchedLocation;
      return AuthGuard.redirect(auth: auth, location: location);
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const SplashPage()),
      GoRoute(path: '/onboarding', builder: (_, _) => const OnboardingPage()),
      GoRoute(path: '/login', builder: (_, _) => const LoginPage()),
      GoRoute(path: '/register', builder: (_, _) => const RegisterPage()),
      GoRoute(
        path: '/forgot-password',
        builder: (_, _) => const ForgotPasswordPage(),
      ),
      ShellRoute(
        builder: (_, _, child) => AppNavigation(child: child),
        routes: [
          GoRoute(path: '/home', builder: (_, _) => const HomePage()),
          GoRoute(path: '/analyze', builder: (_, _) => const AnalyzerPage()),
          GoRoute(path: '/downloads', builder: (_, _) => const DownloadsPage()),
          GoRoute(path: '/library', builder: (_, _) => const LibraryPage()),
          GoRoute(path: '/favorites', builder: (_, _) => const FavoritesPage()),
          GoRoute(path: '/history', builder: (_, _) => const HistoryPage()),
          GoRoute(path: '/settings', builder: (_, _) => const SettingsPage()),
          GoRoute(path: '/playlists', builder: (_, _) => const PlaylistsPage()),
          GoRoute(
            path: '/playlists/:playlistId',
            builder: (_, state) => PlaylistDetailsPage(
              playlistId: state.pathParameters['playlistId']!,
            ),
          ),
          GoRoute(path: '/player', builder: (_, _) => const PlayerPage()),
        ],
      ),
    ],
  );
});

class _RouterRefresh extends ChangeNotifier {
  _RouterRefresh(Stream<AuthState> stream) {
    _subscription = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<AuthState> _subscription;
  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}

class AppNavigation extends StatelessWidget {
  const AppNavigation({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = [
      '/home',
      '/downloads',
      '/library',
      '/favorites',
      '/settings',
    ].indexWhere((path) => location.startsWith(path));
    final strings = AppLocalizations.of(context);
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index < 0 ? 0 : index,
        onDestinationSelected: (value) => context.go(
          ['/home', '/downloads', '/library', '/favorites', '/settings'][value],
        ),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_rounded),
            label: strings.home,
          ),
          NavigationDestination(
            icon: const Icon(Icons.download_rounded),
            label: strings.downloads,
          ),
          NavigationDestination(
            icon: const Icon(Icons.folder_rounded),
            label: strings.library,
          ),
          NavigationDestination(
            icon: const Icon(Icons.favorite_rounded),
            label: strings.favorites,
          ),
          NavigationDestination(
            icon: const Icon(Icons.settings_rounded),
            label: strings.settings,
          ),
        ],
      ),
    );
  }
}

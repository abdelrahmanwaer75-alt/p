import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/auth_providers.dart';
import '../features/auth/auth_pages.dart';
import '../features/home/home_page.dart';
import '../features/analyzer/analyzer_page.dart';
import '../features/downloads/downloads_page.dart';
import '../features/library/library_page.dart';
import '../features/favorites/favorites_page.dart';
import '../features/history/history_page.dart';
import '../features/settings/settings_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final refresh = _RouterRefresh(ref.read(authProvider.notifier).stream);
  ref.onDispose(refresh.dispose);
  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final location = state.matchedLocation;
      final protected = location == '/home' || location.startsWith('/analyze') || location.startsWith('/downloads') || location.startsWith('/library') || location.startsWith('/favorites') || location.startsWith('/history') || location.startsWith('/settings');
      if (auth.status == AuthStatus.restoring && location != '/splash') return '/splash';
      if (auth.status == AuthStatus.restoring) return null;
      if (auth.status == AuthStatus.authenticated && (location == '/splash' || location == '/onboarding' || location == '/login' || location == '/register')) return '/home';
      if (auth.status != AuthStatus.authenticated && protected) return '/login';
      if (auth.status == AuthStatus.unauthenticated && location == '/splash') return '/onboarding';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, __) => const SplashPage()),
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingPage()),
      GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterPage()),
      GoRoute(path: '/forgot-password', builder: (_, __) => const ForgotPasswordPage()),
      ShellRoute(builder: (_, __, child) => AppNavigation(child: child), routes: [
        GoRoute(path: '/home', builder: (_, __) => const HomePage()),
        GoRoute(path: '/analyze', builder: (_, __) => const AnalyzerPage()),
        GoRoute(path: '/downloads', builder: (_, __) => const DownloadsPage()),
        GoRoute(path: '/library', builder: (_, __) => const LibraryPage()),
        GoRoute(path: '/favorites', builder: (_, __) => const FavoritesPage()),
        GoRoute(path: '/history', builder: (_, __) => const HistoryPage()),
        GoRoute(path: '/settings', builder: (_, __) => const SettingsPage()),
      ]),
    ],
  );
});

class _RouterRefresh extends ChangeNotifier {
  _RouterRefresh(Stream<AuthState> stream) { _subscription = stream.listen((_) => notifyListeners()); }
  late final StreamSubscription<AuthState> _subscription;
  @override
  void dispose() { _subscription.cancel(); super.dispose(); }
}

class AppNavigation extends StatelessWidget {
  const AppNavigation({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final index = ['/home', '/downloads', '/library', '/favorites', '/settings'].indexWhere((path) => location.startsWith(path));
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index < 0 ? 0 : index,
        onDestinationSelected: (value) => context.go(['/home', '/downloads', '/library', '/favorites', '/settings'][value]),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_rounded), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.download_rounded), label: 'Downloads'),
          NavigationDestination(icon: Icon(Icons.folder_rounded), label: 'Library'),
          NavigationDestination(icon: Icon(Icons.favorite_rounded), label: 'Favorites'),
          NavigationDestination(icon: Icon(Icons.settings_rounded), label: 'Settings'),
        ],
      ),
    );
  }
}

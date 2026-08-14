import '../features/auth/auth_providers.dart';

class AuthGuard {
  const AuthGuard._();

  static bool isProtected(String location) =>
      location == '/home' ||
      location.startsWith('/analyze') ||
      location.startsWith('/downloads') ||
      location.startsWith('/library') ||
      location.startsWith('/favorites') ||
      location.startsWith('/history') ||
      location.startsWith('/settings') ||
      location.startsWith('/playlists') ||
      location.startsWith('/player');

  static String? redirect({required AuthState auth, required String location}) {
    final protected = isProtected(location);
    if (auth.status == AuthStatus.restoring && location != '/splash') {
      return '/splash';
    }
    if (auth.status == AuthStatus.restoring) return null;
    if (auth.status == AuthStatus.authenticated &&
        (location == '/splash' ||
            location == '/onboarding' ||
            location == '/login' ||
            location == '/register')) {
      return '/home';
    }
    if (auth.status != AuthStatus.authenticated && protected) return '/login';
    if (auth.status == AuthStatus.unauthenticated && location == '/splash') {
      return '/onboarding';
    }
    return null;
  }
}

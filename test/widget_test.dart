import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'package:vidora/app.dart';
import 'package:vidora/core/models/models.dart';
import 'package:vidora/core/network/api_client.dart';
import 'package:vidora/features/auth/auth_pages.dart';
import 'package:vidora/features/auth/auth_providers.dart';
import 'package:vidora/navigation/app_router.dart';

class _UnauthenticatedApiClient extends ApiClient {
  @override
  Future<AuthSession> restoreSession() async {
    throw const ApiFailure(FailureKind.unauthorized, 'No saved session');
  }

  @override
  Future<void> clearSession() async {}
}

void main() {
  testWidgets('Vidora starts at onboarding and routes to sign in', (
    WidgetTester tester,
  ) async {
    final testRouter = GoRouter(
      initialLocation: '/onboarding',
      routes: [
        GoRoute(path: '/onboarding', builder: (_, _) => const OnboardingPage()),
        GoRoute(path: '/login', builder: (_, _) => const LoginPage()),
        GoRoute(
          path: '/forgot-password',
          builder: (_, _) => const ForgotPasswordPage(),
        ),
        GoRoute(path: '/register', builder: (_, _) => const RegisterPage()),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(_UnauthenticatedApiClient()),
          routerProvider.overrideWithValue(testRouter),
        ],
        child: const VidoraApp(),
      ),
    );
    await tester.pump(const Duration(seconds: 2));
    expect(find.text('Vidora'), findsOneWidget);
    expect(
      find.text('Download and organize authorized media.'),
      findsOneWidget,
    );
    expect(find.text('Get started'), findsOneWidget);

    await tester.tap(find.byType(FilledButton));
    await tester.pumpAndSettle();
    expect(find.text('Sign in'), findsNWidgets(2));
  });
}

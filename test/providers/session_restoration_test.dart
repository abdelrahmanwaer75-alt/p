import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:vidora/core/config/app_config.dart';
import 'package:vidora/core/models/models.dart';
import 'package:vidora/core/network/api_client.dart';
import 'package:vidora/features/auth/auth_providers.dart';

class FakeApiClient extends ApiClient {
  FakeApiClient({this.restoreError}) : super(dio: Dio());
  final ApiFailure? restoreError;
  var cleared = false;
  @override
  Future<AuthSession> restoreSession() async {
    if (restoreError != null) throw restoreError!;
    return AuthSession(user: const User(id: 'user-1', email: 'user@example.com'), accessToken: 'access', refreshToken: 'refresh', expiresIn: 900);
  }
  @override
  Future<void> clearSession() async { cleared = true; }
}

void main() {
  test('session restoration reaches authenticated state after secure-token validation', () async {
    final api = FakeApiClient();
    final controller = AuthController(api);
    await controller.restore();
    expect(controller.state.status, AuthStatus.authenticated);
    expect(controller.state.session?.user.email, 'user@example.com');
    controller.dispose();
  });

  test('expired session clears secure storage and becomes unauthenticated', () async {
    final api = FakeApiClient(restoreError: const ApiFailure(FailureKind.unauthorized, 'expired'));
    final controller = AuthController(api);
    await controller.restore();
    expect(controller.state.status, AuthStatus.unauthenticated);
    expect(api.cleared, isTrue);
    controller.dispose();
  });

  test('API URL is configured through API_BASE_URL with no 127.0.0.1 default', () {
    expect(AppConfig.apiBaseUrl, isNot(contains('127.0.0.1')));
  });
}

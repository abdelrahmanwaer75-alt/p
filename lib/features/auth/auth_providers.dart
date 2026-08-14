import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/models/models.dart';
import '../../shared/state/resource_state.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

enum AuthStatus { restoring, unauthenticated, authenticated, error }

class AuthState {
  const AuthState({this.status = AuthStatus.restoring, this.session, this.message});
  final AuthStatus status;
  final AuthSession? session;
  final String? message;
  AuthState copyWith({AuthStatus? status, AuthSession? session, String? message}) => AuthState(status: status ?? this.status, session: session ?? this.session, message: message ?? this.message);
}

final authProvider = StateNotifierProvider<AuthController, AuthState>((ref) => AuthController(ref.read(apiClientProvider)));

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._api) : super(const AuthState()) {
    unawaited(restore());
  }
  final ApiClient _api;

  Future<void> restore() async {
    state = state.copyWith(status: AuthStatus.restoring, message: null);
    try {
      state = state.copyWith(status: AuthStatus.authenticated, session: await _api.restoreSession());
    } on ApiFailure catch (failure) {
      await _api.clearSession();
      state = AuthState(status: failure.kind == FailureKind.unauthorized ? AuthStatus.unauthenticated : AuthStatus.error, message: failure.message);
    } catch (error) {
      await _api.clearSession();
      state = AuthState(status: AuthStatus.error, message: error.toString());
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(status: AuthStatus.restoring, message: null);
    try {
      state = state.copyWith(status: AuthStatus.authenticated, session: await _api.login(email, password));
    } on ApiFailure catch (failure) {
      state = AuthState(status: failure.kind == FailureKind.unauthorized ? AuthStatus.unauthenticated : AuthStatus.error, message: failure.message);
    }
  }

  Future<void> register(String email, String password) async {
    state = state.copyWith(status: AuthStatus.restoring, message: null);
    try {
      state = state.copyWith(status: AuthStatus.authenticated, session: await _api.register(email, password));
    } on ApiFailure catch (failure) {
      state = AuthState(status: AuthStatus.error, message: failure.message);
    }
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}

final sessionProvider = Provider<AuthSession?>((ref) => ref.watch(authProvider).session);

ResourceStatus statusForFailure(ApiFailure failure) => switch (failure.kind) {
  FailureKind.unauthorized => ResourceStatus.unauthorized,
  FailureKind.offline => ResourceStatus.offline,
  _ => ResourceStatus.error,
};

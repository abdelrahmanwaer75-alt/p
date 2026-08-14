import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AnalyzerPreview {
  final String platform;
  final String message;
  final bool supported;
  final String contentKind;

  const AnalyzerPreview({
    required this.platform,
    required this.message,
    required this.supported,
    required this.contentKind,
  });

  factory AnalyzerPreview.fromJson(Map<String, dynamic> json) =>
      AnalyzerPreview(
        platform: json['platform'] as String? ?? 'generic',
        message: json['message'] as String? ?? '',
        supported: json['supported'] as bool? ?? false,
        contentKind: json['content_kind'] as String? ?? 'unknown',
      );
}

class UserSession {
  final String id;
  final String email;
  final String token;
  const UserSession({
    required this.id,
    required this.email,
    required this.token,
  });

  factory UserSession.fromLogin(Map<String, dynamic> json) {
    final user = (json['user'] as Map<String, dynamic>? ?? const {});
    return UserSession(
      id: user['id'] as String? ?? '',
      email: user['email'] as String? ?? '',
      token: json['access_token'] as String? ?? '',
    );
  }
}

class SessionStore {
  const SessionStore();
  static const _tokenKey = 'vidora_access_token';
  static const _emailKey = 'vidora_account_email';
  static const _storage = FlutterSecureStorage();

  Future<void> save(UserSession session) async {
    await _storage.write(key: _tokenKey, value: session.token);
    await _storage.write(key: _emailKey, value: session.email);
  }

  Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _emailKey);
  }
}

class VidoraApiClient {
  final Dio _dio;
  final SessionStore sessionStore;
  String? _token;

  VidoraApiClient({String? baseUrl, this.sessionStore = const SessionStore()})
    : _dio = Dio(
        BaseOptions(
          baseUrl:
              baseUrl ??
              const String.fromEnvironment(
                'VIDORA_API_URL',
                defaultValue: 'http://127.0.0.1:8000',
              ),
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        ),
      );

  Future<UserSession> login(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {'email': email, 'password': password},
    );
    final session = UserSession.fromLogin(response.data ?? const {});
    _token = session.token;
    await sessionStore.save(session);
    return session;
  }

  Future<UserSession> register(String email, String password) async {
    await _dio.post(
      '/api/v1/auth/register',
      data: {'email': email, 'password': password},
    );
    return login(email, password);
  }

  Future<AnalyzerPreview> previewUrl(String url) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/analyzer/preview',
      data: {'url': url},
      options: Options(
        headers: _token == null ? null : {'Authorization': 'Bearer $_token'},
      ),
    );
    return AnalyzerPreview.fromJson(response.data ?? const {});
  }

  Future<void> logout() async {
    _token = null;
    await sessionStore.clear();
  }
}

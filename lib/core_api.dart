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

class DownloadTask {
  final String id;
  final String sourceUrl;
  final String formatId;
  final String status;
  final double? progressPercent;
  final bool progressKnown;
  final String? errorMessage;

  const DownloadTask({
    required this.id,
    required this.sourceUrl,
    required this.formatId,
    required this.status,
    required this.progressPercent,
    required this.progressKnown,
    required this.errorMessage,
  });

  factory DownloadTask.fromJson(Map<String, dynamic> json) => DownloadTask(
    id: json['id'] as String? ?? '',
    sourceUrl: json['source_url'] as String? ?? '',
    formatId: json['format_id'] as String? ?? '',
    status: json['status'] as String? ?? 'queued',
    progressPercent: (json['progress_percent'] as num?)?.toDouble(),
    progressKnown: json['progress_known'] as bool? ?? false,
    errorMessage: json['error_message'] as String?,
  );
}

class LibraryItem {
  final String id;
  final String title;
  final String sourceUrl;
  final String mediaType;
  final bool isFavorite;
  final DateTime? viewedAt;

  const LibraryItem({
    required this.id,
    required this.title,
    required this.sourceUrl,
    required this.mediaType,
    required this.isFavorite,
    required this.viewedAt,
  });

  factory LibraryItem.fromJson(Map<String, dynamic> json) => LibraryItem(
    id: json['id'] as String? ?? '',
    title: json['title'] as String? ?? 'Untitled',
    sourceUrl: json['source_url'] as String? ?? '',
    mediaType: json['media_type'] as String? ?? 'video',
    isFavorite: json['is_favorite'] as bool? ?? false,
    viewedAt: json['viewed_at'] == null
        ? null
        : DateTime.tryParse(json['viewed_at'] as String),
  );
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

  Map<String, String> get _authHeaders =>
      _token == null ? const {} : {'Authorization': 'Bearer $_token'};

  Future<List<LibraryItem>> _getLibrary(String path) async {
    final response = await _dio.get<List<dynamic>>(
      path,
      options: Options(headers: _authHeaders),
    );
    return (response.data ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(LibraryItem.fromJson)
        .toList();
  }

  Future<DownloadTask> createDownload(
    String url,
    String formatId, {
    required bool authorized,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/downloads',
      data: {
        'source_url': url,
        'format_id': formatId,
        'authorized': authorized,
      },
      options: Options(headers: _authHeaders),
    );
    final task = (response.data?['task'] as Map<String, dynamic>?) ?? const {};
    return DownloadTask.fromJson(task);
  }

  Future<List<DownloadTask>> downloads() async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/downloads',
      options: Options(headers: _authHeaders),
    );
    return (response.data ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(DownloadTask.fromJson)
        .toList();
  }

  Future<DownloadTask> downloadStatus(String id) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/downloads/$id',
      options: Options(headers: _authHeaders),
    );
    return DownloadTask.fromJson(response.data ?? const {});
  }

  Future<List<LibraryItem>> library() => _getLibrary('/api/v1/library');
  Future<List<LibraryItem>> files() => _getLibrary('/api/v1/files');
  Future<List<LibraryItem>> favorites() => _getLibrary('/api/v1/favorites');
  Future<List<LibraryItem>> history() => _getLibrary('/api/v1/history');

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

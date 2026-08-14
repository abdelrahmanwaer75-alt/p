import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../models/models.dart';
import '../storage/session_storage.dart';

enum FailureKind { unauthorized, offline, server, validation, unknown }

class ApiFailure implements Exception {
  const ApiFailure(this.kind, this.message, {this.statusCode});
  final FailureKind kind;
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({Dio? dio, SessionStorage? storage, String? baseUrl})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: baseUrl ?? AppConfig.apiBaseUrl,
              headers: {'Content-Type': 'application/json'},
            ),
          ),
      _storage = storage ?? const SessionStorage();

  final Dio _dio;
  final SessionStorage _storage;
  String? _accessToken;
  String? _refreshToken;

  String? get accessToken => _accessToken;
  Dio get dio => _dio;

  Options _options() => Options(
    headers: _accessToken == null
        ? null
        : {'Authorization': 'Bearer $_accessToken'},
  );

  Future<AuthSession> login(String email, String password) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: {'email': email, 'password': password},
      ),
    );
    return _saveSession(AuthSession.fromJson(response.data ?? const {}));
  }

  Future<AuthSession> register(String email, String password) async {
    await _request(
      () => _dio.post(
        '/api/v1/auth/register',
        data: {'email': email, 'password': password},
      ),
    );
    return login(email, password);
  }

  Future<User> currentUser() async {
    final response = await _request(
      () => _dio.get<Map<String, dynamic>>(
        '/api/v1/user/me',
        options: _options(),
      ),
    );
    return User.fromJson(response.data ?? const {});
  }

  Future<AuthSession> restoreSession() async {
    try {
      _accessToken = await _storage.readAccessToken();
      _refreshToken = await _storage.readRefreshToken();
    } catch (_) {
      throw const ApiFailure(FailureKind.unauthorized, 'No saved session');
    }
    if (_accessToken == null || _accessToken!.isEmpty) {
      throw const ApiFailure(FailureKind.unauthorized, 'No saved session');
    }
    try {
      final user = await currentUser();
      return AuthSession(
        user: user,
        accessToken: _accessToken!,
        refreshToken: _refreshToken ?? '',
        expiresIn: 0,
      );
    } on ApiFailure catch (failure) {
      if (failure.kind == FailureKind.unauthorized) await clearSession();
      rethrow;
    }
  }

  Future<AuthSession> refresh() async {
    final refreshToken = _refreshToken ?? await _storage.readRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      throw const ApiFailure(
        FailureKind.unauthorized,
        'Refresh token is missing',
      );
    }
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      ),
    );
    return _saveSession(AuthSession.fromJson(response.data ?? const {}));
  }

  Future<void> logout() async {
    try {
      if (_accessToken != null && _refreshToken != null) {
        await _request(
          () => _dio.post(
            '/api/v1/auth/logout',
            data: {'refresh_token': _refreshToken},
            options: _options(),
          ),
        );
      }
    } finally {
      await clearSession();
    }
  }

  Future<void> clearSession() async {
    _accessToken = null;
    _refreshToken = null;
    await _storage.clear();
  }

  Future<AnalyzerResult> analyze(String url) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/analyzer/preview',
        data: {'url': url},
        options: _options(),
      ),
    );
    return AnalyzerResult.fromJson(response.data ?? const {});
  }

  Future<DownloadTask> createDownload(
    AnalyzerResult analysis,
    MediaFormat format, {
    required bool authorized,
    String? idempotencyKey,
  }) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/downloads',
        data: {
          'source_url': analysis.url,
          'platform': analysis.platform,
          'title': analysis.title,
          'format_id': format.formatId,
          'format_type': format.kind,
          'extension': format.extension,
          'mime_type': format.mimeType,
          'quality': format.quality,
          'authorized': authorized,
        },
        options: _options().copyWith(
          headers: {...?_options().headers, 'Idempotency-Key': ?idempotencyKey},
        ),
      ),
    );
    return DownloadTask.fromJson(
      (response.data?['task'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<List<DownloadTask>> downloads() async {
    final response = await _request(
      () => _dio.get<List<dynamic>>('/api/v1/downloads', options: _options()),
    );
    return _objects(response.data).map(DownloadTask.fromJson).toList();
  }

  Future<DownloadTask> pauseDownload(String id) async =>
      _downloadAction(id, 'pause');
  Future<DownloadTask> resumeDownload(String id) async =>
      _downloadAction(id, 'resume');
  Future<DownloadTask> retryDownload(String id) async =>
      _downloadAction(id, 'retry');
  Future<DownloadTask> openDownload(String id) async =>
      _downloadAction(id, 'open');
  Future<DownloadTask> _downloadAction(String id, String action) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/downloads/$id/$action',
        options: _options(),
      ),
    );
    return DownloadTask.fromJson(response.data ?? const {});
  }

  Future<void> deleteDownload(String id) async {
    await _request(
      () => _dio.delete('/api/v1/downloads/$id', options: _options()),
    );
  }

  Future<DownloadTask> cancelDownload(String id) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/downloads/$id/cancel',
        options: _options(),
      ),
    );
    return DownloadTask.fromJson(
      (response.data?['task'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<List<ManagedFile>> files({
    String? search,
    String sort = 'date',
    bool descending = true,
  }) async {
    final response = await _request(
      () => _dio.get<List<dynamic>>(
        '/api/v1/files',
        queryParameters: {
          'search': search,
          'sort': sort,
          'descending': descending,
        },
        options: _options(),
      ),
    );
    return _objects(response.data).map(ManagedFile.fromJson).toList();
  }

  Future<ManagedFile> renameFile(String id, String filename) async =>
      _fileAction('/api/v1/files/$id/rename', {'filename': filename});
  Future<ManagedFile> moveFile(String id, String folder) async =>
      _fileAction('/api/v1/files/$id/move', {'folder': folder});
  Future<void> deleteFile(String id) async {
    await _request(() => _dio.delete('/api/v1/files/$id', options: _options()));
  }

  Future<ManagedFile> _fileAction(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        path,
        data: data,
        options: _options(),
      ),
    );
    return ManagedFile.fromJson(
      (response.data?['file'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<ManagedFile> fileInfo(String id) async {
    final response = await _request(
      () => _dio.get<Map<String, dynamic>>(
        '/api/v1/files/$id',
        options: _options(),
      ),
    );
    return ManagedFile.fromJson(
      (response.data?['file'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<ManagedFile> openFile(String id) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/files/$id/open',
        options: _options(),
      ),
    );
    return ManagedFile.fromJson(
      (response.data?['file'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<LibraryItem> setFavorite(String id, bool favorite) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/library/$id/favorite',
        data: {'favorite': favorite},
        options: _options(),
      ),
    );
    return LibraryItem.fromJson(response.data ?? const {});
  }

  Future<ManagedFile> shareFile(String id) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/files/$id/share',
        options: _options(),
      ),
    );
    return ManagedFile.fromJson(
      (response.data?['file'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  Future<List<Playlist>> playlists() async {
    final response = await _request(
      () => _dio.get<List<dynamic>>('/api/v1/playlists', options: _options()),
    );
    return _objects(response.data).map(Playlist.fromJson).toList();
  }

  Future<Playlist> createPlaylist(String name, {String? description}) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/playlists',
        data: {'name': name, 'description': description},
        options: _options(),
      ),
    );
    return Playlist.fromJson(response.data ?? const {});
  }

  Future<Playlist> updatePlaylist(
    String id, {
    String? name,
    String? description,
  }) async {
    final response = await _request(
      () => _dio.patch<Map<String, dynamic>>(
        '/api/v1/playlists/$id',
        data: {'name': name, 'description': description},
        options: _options(),
      ),
    );
    return Playlist.fromJson(response.data ?? const {});
  }

  Future<void> deletePlaylist(String id) async {
    await _request(
      () => _dio.delete('/api/v1/playlists/$id', options: _options()),
    );
  }

  Future<Playlist> addPlaylistItem(
    String playlistId,
    String libraryItemId, {
    int? position,
  }) async => _playlistAction('/api/v1/playlists/$playlistId/items', {
    'library_item_id': libraryItemId,
    'position': position,
  });
  Future<Playlist> removePlaylistItem(String playlistId, String itemId) async {
    final response = await _request(
      () => _dio.delete<Map<String, dynamic>>(
        '/api/v1/playlists/$playlistId/items/$itemId',
        options: _options(),
      ),
    );
    return Playlist.fromJson(response.data ?? const {});
  }

  Future<Playlist> reorderPlaylist(String id, List<String> itemIds) async =>
      _playlistAction('/api/v1/playlists/$id/reorder', {'item_ids': itemIds});
  Future<Playlist> playPlaylist(String id) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/playlists/$id/play',
        options: _options(),
      ),
    );
    return Playlist.fromJson(response.data ?? const {});
  }

  Future<void> downloadPlaylist(String id) async {
    await _request(
      () => _dio.post('/api/v1/playlists/$id/download', options: _options()),
    );
  }

  Future<Playlist> _playlistAction(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await _request(
      () => _dio.post<Map<String, dynamic>>(
        path,
        data: data,
        options: _options(),
      ),
    );
    return Playlist.fromJson(response.data ?? const {});
  }

  Future<List<LibraryItem>> library() => _library('/api/v1/library');
  Future<List<LibraryItem>> favorites() => _library('/api/v1/favorites');
  Future<List<LibraryItem>> history() => _library('/api/v1/history');

  Future<List<LibraryItem>> _library(String path) async {
    final response = await _request(
      () => _dio.get<List<dynamic>>(path, options: _options()),
    );
    return _objects(response.data).map(LibraryItem.fromJson).toList();
  }

  Future<AuthSession> _saveSession(AuthSession session) async {
    _accessToken = session.accessToken;
    _refreshToken = session.refreshToken;
    await _storage.save(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      email: session.user.email,
    );
    return session;
  }

  Future<Response<T>> _request<T>(
    Future<Response<T>> Function() request,
  ) async {
    try {
      return await request();
    } on DioException catch (error) {
      final status = error.response?.statusCode;
      final kind = status == 401
          ? FailureKind.unauthorized
          : status != null && status >= 400 && status < 500
          ? FailureKind.validation
          : status != null && status >= 500
          ? FailureKind.server
          : error.type == DioExceptionType.connectionError ||
                error.type == DioExceptionType.connectionTimeout
          ? FailureKind.offline
          : FailureKind.unknown;
      final data = error.response?.data;
      final message = data is Map && data['detail'] is String
          ? data['detail'] as String
          : error.message ?? 'Request failed';
      throw ApiFailure(kind, message, statusCode: status);
    }
  }

  static List<Map<String, dynamic>> _objects(Object? value) => value is List
      ? value
            .whereType<Map>()
            .map((item) => item.cast<String, dynamic>())
            .toList()
      : <Map<String, dynamic>>[];
}

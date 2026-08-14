import 'package:freezed_annotation/freezed_annotation.dart';

part 'models.freezed.dart';
part 'models.g.dart';

// These source models are intentionally explicit and immutable. The repository
// keeps the Freezed/json_serializable parts so generated code can be refreshed
// with build_runner in a Flutter-enabled environment.

@Freezed()
class User {
  const User({required this.id, required this.email, this.createdAt, this.updatedAt, this.isActive = true, this.isVerified = false});
  final String id;
  final String email;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final bool isActive;
  final bool isVerified;

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'] as String? ?? '', email: json['email'] as String? ?? '',
    createdAt: _date(json['created_at']), updatedAt: _date(json['updated_at']),
    isActive: json['is_active'] as bool? ?? true, isVerified: json['is_verified'] as bool? ?? false,
  );
  Map<String, dynamic> toJson() => {'id': id, 'email': email, 'created_at': createdAt?.toIso8601String(), 'updated_at': updatedAt?.toIso8601String(), 'is_active': isActive, 'is_verified': isVerified};
}

@Freezed()
class AuthSession {
  const AuthSession({required this.user, required this.accessToken, required this.refreshToken, required this.expiresIn});
  final User user;
  final String accessToken;
  final String refreshToken;
  final int expiresIn;

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
    user: User.fromJson((json['user'] as Map?)?.cast<String, dynamic>() ?? const {}),
    accessToken: json['access_token'] as String? ?? '', refreshToken: json['refresh_token'] as String? ?? '',
    expiresIn: (json['expires_in'] as num?)?.toInt() ?? 900,
  );
  Map<String, dynamic> toJson() => {'user': user.toJson(), 'access_token': accessToken, 'refresh_token': refreshToken, 'expires_in': expiresIn};
}

@Freezed()
class MediaFormat {
  const MediaFormat({required this.formatId, required this.extension, required this.kind, this.resolution, this.quality, this.mimeType, this.estimatedSizeBytes});
  final String formatId;
  final String extension;
  final String kind;
  final String? resolution;
  final String? quality;
  final String? mimeType;
  final int? estimatedSizeBytes;

  factory MediaFormat.fromJson(Map<String, dynamic> json) => MediaFormat(
    formatId: json['format_id'] as String? ?? '', extension: json['extension'] as String? ?? '', kind: json['kind'] as String? ?? 'unknown',
    resolution: json['resolution'] as String?, quality: json['quality'] as String?, mimeType: json['mime_type'] as String?, estimatedSizeBytes: (json['estimated_size_bytes'] as num?)?.toInt(),
  );
  Map<String, dynamic> toJson() => {'format_id': formatId, 'extension': extension, 'kind': kind, 'resolution': resolution, 'quality': quality, 'mime_type': mimeType, 'estimated_size_bytes': estimatedSizeBytes};
}

@Freezed()
class AnalyzerResult {
  const AnalyzerResult({required this.url, required this.platform, required this.supported, required this.message, this.title, this.description, this.thumbnail, this.duration, this.uploader, this.formats = const [], this.audioFormats = const [], this.videoFormats = const [], this.restrictions = const []});
  final String url;
  final String platform;
  final bool supported;
  final String message;
  final String? title;
  final String? description;
  final String? thumbnail;
  final int? duration;
  final String? uploader;
  final List<MediaFormat> formats;
  final List<MediaFormat> audioFormats;
  final List<MediaFormat> videoFormats;
  final List<String> restrictions;

  factory AnalyzerResult.fromJson(Map<String, dynamic> json) => AnalyzerResult(
    url: json['url'] as String? ?? '', platform: json['platform'] as String? ?? 'generic', supported: json['supported'] as bool? ?? false, message: json['message'] as String? ?? '',
    title: json['title'] as String?, description: json['description'] as String?, thumbnail: json['thumbnail'] as String?, duration: (json['duration'] as num?)?.toInt(), uploader: json['uploader'] as String?,
    formats: _list(json['formats']).map(MediaFormat.fromJson).toList(), audioFormats: _list(json['audio_formats']).map(MediaFormat.fromJson).toList(), videoFormats: _list(json['video_formats']).map(MediaFormat.fromJson).toList(), restrictions: _stringList(json['restrictions']),
  );
  Map<String, dynamic> toJson() => {'url': url, 'platform': platform, 'supported': supported, 'message': message, 'title': title, 'description': description, 'thumbnail': thumbnail, 'duration': duration, 'uploader': uploader, 'formats': formats.map((e) => e.toJson()).toList(), 'audio_formats': audioFormats.map((e) => e.toJson()).toList(), 'video_formats': videoFormats.map((e) => e.toJson()).toList(), 'restrictions': restrictions};
}

@Freezed()
class DownloadTask {
  const DownloadTask({required this.id, required this.userId, required this.sourceUrl, required this.platform, required this.formatId, required this.status, this.title, this.thumbnail, this.progress, this.bytesDownloaded = 0, this.totalBytes, this.speed, this.eta, this.outputPath, this.outputFilename, this.errorCode, this.errorMessage, this.createdAt, this.startedAt, this.completedAt, this.cancelledAt, this.updatedAt, this.retryCount = 0});
  final String id;
  final String userId;
  final String sourceUrl;
  final String platform;
  final String formatId;
  final String status;
  final String? title;
  final String? thumbnail;
  final double? progress;
  final int bytesDownloaded;
  final int? totalBytes;
  final double? speed;
  final int? eta;
  final String? outputPath;
  final String? outputFilename;
  final String? errorCode;
  final String? errorMessage;
  final DateTime? createdAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime? cancelledAt;
  final DateTime? updatedAt;
  final int retryCount;

  factory DownloadTask.fromJson(Map<String, dynamic> json) => DownloadTask(
    id: json['id'] as String? ?? '', userId: (json['user_id'] ?? json['owner_id']) as String? ?? '', sourceUrl: json['source_url'] as String? ?? '', platform: json['platform'] as String? ?? 'generic', formatId: json['format_id'] as String? ?? '', status: json['status'] as String? ?? 'queued', title: json['title'] as String?, thumbnail: json['thumbnail'] as String?, progress: (json['progress_percent'] as num?)?.toDouble(), bytesDownloaded: (json['bytes_downloaded'] as num?)?.toInt() ?? 0, totalBytes: (json['total_bytes'] as num?)?.toInt(), speed: (json['speed'] as num?)?.toDouble(), eta: (json['eta'] as num?)?.toInt(), outputPath: json['output_path'] as String?, outputFilename: json['output_filename'] as String?, errorCode: json['error_code'] as String?, errorMessage: json['error_message'] as String?, createdAt: _date(json['created_at']), startedAt: _date(json['started_at']), completedAt: _date(json['completed_at']), cancelledAt: _date(json['cancelled_at']), updatedAt: _date(json['updated_at']), retryCount: (json['retry_count'] as num?)?.toInt() ?? 0,
  );
  Map<String, dynamic> toJson() => {'id': id, 'user_id': userId, 'source_url': sourceUrl, 'platform': platform, 'format_id': formatId, 'status': status, 'title': title, 'thumbnail': thumbnail, 'progress_percent': progress, 'bytes_downloaded': bytesDownloaded, 'total_bytes': totalBytes, 'speed': speed, 'eta': eta, 'output_path': outputPath, 'output_filename': outputFilename, 'error_code': errorCode, 'error_message': errorMessage, 'created_at': createdAt?.toIso8601String(), 'started_at': startedAt?.toIso8601String(), 'completed_at': completedAt?.toIso8601String(), 'cancelled_at': cancelledAt?.toIso8601String(), 'updated_at': updatedAt?.toIso8601String(), 'retry_count': retryCount};
}

@Freezed()
class LibraryItem {
  const LibraryItem({required this.id, required this.ownerId, required this.title, required this.sourceUrl, required this.mediaType, this.mediaPath, this.mimeType, this.fileSize, this.duration, this.thumbnail, this.downloadedAt, this.isFavorite = false, this.viewedAt, this.createdAt});
  final String id;
  final String ownerId;
  final String title;
  final String sourceUrl;
  final String mediaType;
  final String? mediaPath;
  final String? mimeType;
  final int? fileSize;
  final int? duration;
  final String? thumbnail;
  final DateTime? downloadedAt;
  final bool isFavorite;
  final DateTime? viewedAt;
  final DateTime? createdAt;

  factory LibraryItem.fromJson(Map<String, dynamic> json) => LibraryItem(id: json['id'] as String? ?? '', ownerId: json['owner_id'] as String? ?? '', title: json['title'] as String? ?? 'Untitled', sourceUrl: json['source_url'] as String? ?? '', mediaType: json['media_type'] as String? ?? 'video', mediaPath: json['media_path'] as String?, mimeType: json['mime_type'] as String?, fileSize: (json['file_size'] as num?)?.toInt(), duration: (json['duration'] as num?)?.toInt(), thumbnail: json['thumbnail'] as String?, downloadedAt: _date(json['downloaded_at']), isFavorite: json['is_favorite'] as bool? ?? false, viewedAt: _date(json['viewed_at']), createdAt: _date(json['created_at']));
  Map<String, dynamic> toJson() => {'id': id, 'owner_id': ownerId, 'title': title, 'source_url': sourceUrl, 'media_type': mediaType, 'media_path': mediaPath, 'mime_type': mimeType, 'file_size': fileSize, 'duration': duration, 'thumbnail': thumbnail, 'downloaded_at': downloadedAt?.toIso8601String(), 'is_favorite': isFavorite, 'viewed_at': viewedAt?.toIso8601String(), 'created_at': createdAt?.toIso8601String()};
}

@Freezed()
class Favorite {
  const Favorite({required this.id, required this.userId, required this.libraryItemId, this.createdAt});
  final String id;
  final String userId;
  final String libraryItemId;
  final DateTime? createdAt;
  factory Favorite.fromJson(Map<String, dynamic> json) => Favorite(id: json['id'] as String? ?? '', userId: json['user_id'] as String? ?? '', libraryItemId: json['library_item_id'] as String? ?? '', createdAt: _date(json['created_at']));
  Map<String, dynamic> toJson() => {'id': id, 'user_id': userId, 'library_item_id': libraryItemId, 'created_at': createdAt?.toIso8601String()};
}

@Freezed()
class HistoryItem {
  const HistoryItem({required this.id, required this.userId, required this.libraryItemId, this.viewedAt});
  final String id;
  final String userId;
  final String libraryItemId;
  final DateTime? viewedAt;
  factory HistoryItem.fromJson(Map<String, dynamic> json) => HistoryItem(id: json['id'] as String? ?? '', userId: json['user_id'] as String? ?? '', libraryItemId: json['library_item_id'] as String? ?? '', viewedAt: _date(json['viewed_at']));
  Map<String, dynamic> toJson() => {'id': id, 'user_id': userId, 'library_item_id': libraryItemId, 'viewed_at': viewedAt?.toIso8601String()};
}

DateTime? _date(Object? value) => value is String ? DateTime.tryParse(value) : null;
List<Map<String, dynamic>> _list(Object? value) => value is List ? value.whereType<Map>().map((e) => e.cast<String, dynamic>()).toList() : <Map<String, dynamic>>[];
List<String> _stringList(Object? value) => value is List ? value.whereType<String>().toList() : <String>[];


@Freezed()
class ManagedFile {
  const ManagedFile({required this.libraryId, required this.path, required this.mediaPath, required this.filename, required this.size, required this.extension, required this.mediaType, required this.title, this.mimeType, this.duration, this.modifiedAt, this.isFavorite = false});
  final String libraryId;
  final String path;
  final String mediaPath;
  final String filename;
  final int size;
  final String? mimeType;
  final String extension;
  final String mediaType;
  final int? duration;
  final DateTime? modifiedAt;
  final bool isFavorite;

  factory ManagedFile.fromJson(Map<String, dynamic> json) => ManagedFile(libraryId: json['library_id'] as String? ?? '', path: json['path'] as String? ?? '', mediaPath: json['media_path'] as String? ?? '', filename: json['filename'] as String? ?? '', size: (json['size'] as num?)?.toInt() ?? 0, mimeType: json['mime_type'] as String?, extension: json['extension'] as String? ?? '', mediaType: json['media_type'] as String? ?? 'file', duration: (json['duration'] as num?)?.toInt(), modifiedAt: _date(json['modified_at']), isFavorite: json['is_favorite'] as bool? ?? false, title: json['title'] as String? ?? 'Untitled');
  final String title;
  Map<String, dynamic> toJson() => {'library_id': libraryId, 'path': path, 'media_path': mediaPath, 'filename': filename, 'size': size, 'mime_type': mimeType, 'extension': extension, 'media_type': mediaType, 'duration': duration, 'modified_at': modifiedAt?.toIso8601String(), 'is_favorite': isFavorite, 'title': title};
}

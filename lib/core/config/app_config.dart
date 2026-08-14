import '../../config/environment.dart';

class AppConfig {
  const AppConfig._();

  static const apiBaseUrl = Environment.apiBaseUrl;

  static String get websocketBaseUrl {
    final uri = Uri.parse(apiBaseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return uri
        .replace(scheme: scheme)
        .toString()
        .replaceFirst(RegExp(r'/$'), '');
  }

  static String get downloadsWebSocketUrl =>
      '$websocketBaseUrl/api/v1/ws/downloads';
}

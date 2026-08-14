class AppConfig {
  const AppConfig._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static String get websocketBaseUrl {
    final uri = Uri.parse(apiBaseUrl);
    final scheme = uri.scheme == 'https' ? 'wss' : 'ws';
    return uri.replace(scheme: scheme).toString().replaceFirst(RegExp(r'/$'), '');
  }

  static String get downloadsWebSocketUrl => '$websocketBaseUrl/api/v1/ws/downloads';
}

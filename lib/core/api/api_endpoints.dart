class ApiEndpoints {
  const ApiEndpoints._();

  static const authLogin = '/api/v1/auth/login';
  static const authRegister = '/api/v1/auth/register';
  static const authRefresh = '/api/v1/auth/refresh';
  static const authLogout = '/api/v1/auth/logout';
  static const currentUser = '/api/v1/user/me';
  static const analyzerPreview = '/api/v1/analyzer/preview';
  static const downloads = '/api/v1/downloads';
  static const files = '/api/v1/files';
  static const library = '/api/v1/library';
  static const favorites = '/api/v1/favorites';
  static const history = '/api/v1/history';
  static const playlists = '/api/v1/playlists';
  static const downloadsWebSocket = '/api/v1/ws/downloads';
}

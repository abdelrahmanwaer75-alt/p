import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SessionStorage {
  const SessionStorage({this._storage = const FlutterSecureStorage()});

  static const accessTokenKey = 'vidora_access_token';
  static const refreshTokenKey = 'vidora_refresh_token';
  static const emailKey = 'vidora_account_email';
  final FlutterSecureStorage _storage;

  Future<void> save({
    required String accessToken,
    required String refreshToken,
    required String email,
  }) async {
    await _storage.write(key: accessTokenKey, value: accessToken);
    await _storage.write(key: refreshTokenKey, value: refreshToken);
    await _storage.write(key: emailKey, value: email);
  }

  Future<String?> readAccessToken() => _storage.read(key: accessTokenKey);
  Future<String?> readRefreshToken() => _storage.read(key: refreshTokenKey);
  Future<void> clear() async {
    await Future.wait([
      _storage.delete(key: accessTokenKey),
      _storage.delete(key: refreshTokenKey),
      _storage.delete(key: emailKey),
    ]);
  }
}

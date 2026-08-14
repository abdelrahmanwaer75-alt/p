import '../models/models.dart';
import '../network/api_client.dart';

class AuthApi {
  const AuthApi(this._client);
  final ApiClient _client;

  Future<AuthSession> login(String email, String password) =>
      _client.login(email, password);
  Future<AuthSession> register(String email, String password) =>
      _client.register(email, password);
  Future<User> currentUser() => _client.currentUser();
  Future<AuthSession> restoreSession() => _client.restoreSession();
  Future<AuthSession> refresh() => _client.refresh();
  Future<void> logout() => _client.logout();
}

class AnalyzerApi {
  const AnalyzerApi(this._client);
  final ApiClient _client;

  Future<AnalyzerResult> analyze(String url) => _client.analyze(url);
}

class DownloadsApi {
  const DownloadsApi(this._client);
  final ApiClient _client;

  Future<DownloadTask> create(
    AnalyzerResult analysis,
    MediaFormat format, {
    required bool authorized,
    String? idempotencyKey,
  }) => _client.createDownload(
    analysis,
    format,
    authorized: authorized,
    idempotencyKey: idempotencyKey,
  );

  Future<List<DownloadTask>> list() => _client.downloads();
  Future<DownloadTask> pause(String id) => _client.pauseDownload(id);
  Future<DownloadTask> resume(String id) => _client.resumeDownload(id);
  Future<DownloadTask> retry(String id) => _client.retryDownload(id);
  Future<DownloadTask> cancel(String id) => _client.cancelDownload(id);
  Future<void> delete(String id) => _client.deleteDownload(id);
}

class FilesApi {
  const FilesApi(this._client);
  final ApiClient _client;

  Future<List<ManagedFile>> list({
    String sort = 'date',
    bool descending = true,
  }) => _client.files(sort: sort, descending: descending);
  Future<ManagedFile> rename(String id, String filename) =>
      _client.renameFile(id, filename);
  Future<ManagedFile> move(String id, String folder) =>
      _client.moveFile(id, folder);
  Future<void> delete(String id) => _client.deleteFile(id);
  Future<ManagedFile> info(String id) => _client.fileInfo(id);
  Future<ManagedFile> open(String id) => _client.openFile(id);
  Future<LibraryItem> favorite(String id, bool value) =>
      _client.setFavorite(id, value);
  Future<ManagedFile> share(String id) => _client.shareFile(id);
}

class LibraryApi {
  const LibraryApi(this._client);
  final ApiClient _client;

  Future<List<LibraryItem>> list() => _client.library();
}

class FavoritesApi {
  const FavoritesApi(this._client);
  final ApiClient _client;

  Future<List<LibraryItem>> list() => _client.favorites();
}

class HistoryApi {
  const HistoryApi(this._client);
  final ApiClient _client;

  Future<List<LibraryItem>> list() => _client.history();
}

class PlaylistsApi {
  const PlaylistsApi(this._client);
  final ApiClient _client;

  Future<List<Playlist>> list() => _client.playlists();
  Future<Playlist> create(String name, {String? description}) =>
      _client.createPlaylist(name, description: description);
  Future<Playlist> rename(String id, String name) =>
      _client.updatePlaylist(id, name: name);
  Future<void> delete(String id) => _client.deletePlaylist(id);
  Future<Playlist> add(String playlistId, String libraryItemId) =>
      _client.addPlaylistItem(playlistId, libraryItemId);
  Future<Playlist> remove(String playlistId, String itemId) =>
      _client.removePlaylistItem(playlistId, itemId);
  Future<Playlist> reorder(String id, List<String> itemIds) =>
      _client.reorderPlaylist(id, itemIds);
  Future<Playlist> play(String id) => _client.playPlaylist(id);
}

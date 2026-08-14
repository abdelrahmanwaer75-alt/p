import '../../core/models/models.dart';
import '../../core/network/api_client.dart';

/// Application service for file-manager operations.
/// It contains no widget or filesystem code; all remote access stays in ApiClient.
class FileService {
  const FileService(this._api);

  final ApiClient _api;

  Future<List<ManagedFile>> list({
    String? search,
    String sort = 'date',
    bool descending = true,
  }) => _api.files(search: search, sort: sort, descending: descending);

  Future<ManagedFile> rename(String id, String filename) =>
      _api.renameFile(id, filename);

  Future<ManagedFile> move(String id, String folder) =>
      _api.moveFile(id, folder);

  Future<ManagedFile> open(String id) => _api.openFile(id);

  Future<ManagedFile> share(String id) => _api.shareFile(id);

  Future<void> delete(String id) => _api.deleteFile(id);

  Future<void> favorite(String id, bool value) => _api.setFavorite(id, value);
}

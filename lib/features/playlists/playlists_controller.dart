import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/network/api_client.dart';
import '../../shared/state/resource_state.dart';
import '../player/player_provider.dart';
import '../auth/auth_providers.dart';

final playlistsProvider =
    StateNotifierProvider<PlaylistController, ResourceState<List<Playlist>>>(
      (ref) => PlaylistController(
        ref.read(apiClientProvider),
        ref.read(playerProvider.notifier),
      ),
    );

class PlaylistController extends StateNotifier<ResourceState<List<Playlist>>> {
  PlaylistController(this._api, this._player)
    : super(const ResourceState(status: ResourceStatus.loading)) {
    load();
  }
  final ApiClient _api;
  final PlayerController _player;

  Future<void> load() async {
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final values = await _api.playlists();
      state = ResourceState(
        status: values.isEmpty ? ResourceStatus.empty : ResourceStatus.success,
        data: values,
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        message: failure.message,
      );
    }
  }

  Future<Playlist?> create(String name, {String? description}) async {
    try {
      final created = await _api.createPlaylist(name, description: description);
      state = ResourceState(
        status: ResourceStatus.success,
        data: [...?state.data, created],
      );
      return created;
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
      return null;
    }
  }

  Future<void> update(String id, {String? name, String? description}) async {
    try {
      final updated = await _api.updatePlaylist(
        id,
        name: name,
        description: description,
      );
      _replace(updated);
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<void> delete(String id) async {
    try {
      await _api.deletePlaylist(id);
      state = ResourceState(
        status: ResourceStatus.success,
        data: [...?state.data]..removeWhere((playlist) => playlist.id == id),
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<Playlist?> addItem(
    String playlistId,
    String libraryItemId, {
    int? position,
  }) async {
    try {
      final updated = await _api.addPlaylistItem(
        playlistId,
        libraryItemId,
        position: position,
      );
      _replace(updated);
      return updated;
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
      return null;
    }
  }

  Future<void> removeItem(String playlistId, String itemId) async {
    try {
      _replace(await _api.removePlaylistItem(playlistId, itemId));
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<void> reorder(String playlistId, List<String> itemIds) async {
    try {
      _replace(await _api.reorderPlaylist(playlistId, itemIds));
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<void> play(Playlist playlist, {int index = 0}) =>
      _player.playPlaylist(playlist.items, index: index);

  /// Playlist batch downloading is deliberately unavailable until every
  /// requested extractor is implemented and backend-authorized.
  Future<void> requestDownload(String playlistId) async {
    state = ResourceState(
      status: ResourceStatus.error,
      data: state.data,
      message: 'FEATURE_NOT_AVAILABLE: playlist downloads require backend extractor support',
    );
  }

  void _replace(Playlist updated) {
    final values = [...?state.data];
    final index = values.indexWhere((playlist) => playlist.id == updated.id);
    if (index >= 0) values[index] = updated;
    state = ResourceState(status: ResourceStatus.success, data: values);
  }
}

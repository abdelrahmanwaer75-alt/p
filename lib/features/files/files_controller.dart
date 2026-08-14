import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/network/api_client.dart';
import '../../shared/state/resource_state.dart';
import '../auth/auth_providers.dart';

final fileManagerProvider =
    StateNotifierProvider<
      FileManagerController,
      ResourceState<List<ManagedFile>>
    >((ref) => FileManagerController(ref.read(apiClientProvider)));

class FileManagerController
    extends StateNotifier<ResourceState<List<ManagedFile>>> {
  FileManagerController(this._api) : super(const ResourceState()) {
    unawaited(load());
  }

  final ApiClient _api;
  String query = '';
  String sort = 'date';
  bool descending = true;

  Future<void> load({String? search, String? sortBy, bool? desc}) async {
    query = search ?? query;
    sort = sortBy ?? sort;
    descending = desc ?? descending;
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final files = await _api.files(
        search: query.isEmpty ? null : query,
        sort: sort,
        descending: descending,
      );
      state = ResourceState(
        status: files.isEmpty ? ResourceStatus.empty : ResourceStatus.success,
        data: files,
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        message: failure.message,
      );
    }
  }

  Future<void> rename(String id, String filename) async =>
      _apply(id, () => _api.renameFile(id, filename));
  Future<void> move(String id, String folder) async =>
      _apply(id, () => _api.moveFile(id, folder));
  Future<void> open(String id) async => _apply(id, () => _api.openFile(id));
  Future<void> share(String id) async => _apply(id, () => _api.shareFile(id));

  Future<void> favorite(String id, bool value) async {
    try {
      await _api.setFavorite(id, value);
      final files = [...?state.data];
      final index = files.indexWhere((file) => file.libraryId == id);
      if (index >= 0) {
        files[index] = ManagedFile.fromJson({
          ...files[index].toJson(),
          'is_favorite': value,
        });
      }
      state = ResourceState(status: ResourceStatus.success, data: files);
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
      await _api.deleteFile(id);
      state = ResourceState(
        status: ResourceStatus.success,
        data: [...?state.data]..removeWhere((file) => file.libraryId == id),
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<void> _apply(String id, Future<ManagedFile> Function() action) async {
    try {
      final updated = await action();
      final values = [...?state.data];
      final index = values.indexWhere((file) => file.libraryId == id);
      if (index >= 0) values[index] = updated;
      state = ResourceState(status: ResourceStatus.success, data: values);
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }
}

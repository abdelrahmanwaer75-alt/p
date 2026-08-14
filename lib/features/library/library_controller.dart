import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/network/api_client.dart';
import '../../shared/state/resource_state.dart';
import '../auth/auth_providers.dart';

final libraryProvider =
    StateNotifierProvider<LibraryController, ResourceState<List<LibraryItem>>>(
      (ref) => LibraryController(ref.read(apiClientProvider)),
    );
final favoritesProvider =
    StateNotifierProvider<
      CollectionController,
      ResourceState<List<LibraryItem>>
    >(
      (ref) => CollectionController(
        ref.read(apiClientProvider),
        CollectionKind.favorites,
      ),
    );
final historyProvider =
    StateNotifierProvider<
      CollectionController,
      ResourceState<List<LibraryItem>>
    >(
      (ref) => CollectionController(
        ref.read(apiClientProvider),
        CollectionKind.history,
      ),
    );

class LibraryController extends CollectionController {
  LibraryController(ApiClient api) : super(api, CollectionKind.library);
}

enum CollectionKind { library, favorites, history }

class CollectionController
    extends StateNotifier<ResourceState<List<LibraryItem>>> {
  CollectionController(this._api, this._kind) : super(const ResourceState()) {
    unawaited(load());
  }

  final ApiClient _api;
  final CollectionKind _kind;

  Future<void> load() async {
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final values = switch (_kind) {
        CollectionKind.library => await _api.library(),
        CollectionKind.favorites => await _api.favorites(),
        CollectionKind.history => await _api.history(),
      };
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
}

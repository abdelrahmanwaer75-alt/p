import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/network/api_client.dart';
import '../../shared/state/resource_state.dart';
import '../auth/auth_providers.dart';

final analyzerProvider =
    StateNotifierProvider<AnalyzerController, ResourceState<AnalyzerResult>>(
      (ref) => AnalyzerController(ref.read(apiClientProvider)),
    );

class AnalyzerController extends StateNotifier<ResourceState<AnalyzerResult>> {
  AnalyzerController(this._api) : super(const ResourceState());

  final ApiClient _api;

  Future<AnalyzerResult?> analyze(String url) async {
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final result = await _api.analyze(url);
      state = ResourceState(
        status: result.formats.isEmpty && !result.supported
            ? ResourceStatus.empty
            : ResourceStatus.success,
        data: result,
        message: result.message,
      );
      return result;
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        message: failure.message,
      );
      return null;
    }
  }
}

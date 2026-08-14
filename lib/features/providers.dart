import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/config/app_config.dart';
import '../core/downloads/background_download_service.dart';
import '../core/models/models.dart';
import '../core/network/api_client.dart';
import '../shared/state/resource_state.dart';
import 'auth/auth_providers.dart';

final analyzerProvider = StateNotifierProvider<AnalyzerController, ResourceState<AnalyzerResult>>((ref) => AnalyzerController(ref.read(apiClientProvider)));

class AnalyzerController extends StateNotifier<ResourceState<AnalyzerResult>> {
  AnalyzerController(this._api) : super(const ResourceState());
  final ApiClient _api;
  Future<AnalyzerResult?> analyze(String url) async {
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final result = await _api.analyze(url);
      state = ResourceState(status: result.formats.isEmpty && !result.supported ? ResourceStatus.empty : ResourceStatus.success, data: result, message: result.message);
      return result;
    } on ApiFailure catch (failure) {
      state = ResourceState(status: statusForFailure(failure), message: failure.message);
      return null;
    }
  }
}

final downloadsProvider = StateNotifierProvider<DownloadsController, ResourceState<List<DownloadTask>>>((ref) {
  final controller = DownloadsController(ref.read(apiClientProvider), BackgroundDownloadService());
  ref.onDispose(controller.dispose);
  return controller;
});

class DownloadsController extends StateNotifier<ResourceState<List<DownloadTask>>> {
  DownloadsController(this._api, this._background) : super(const ResourceState()) {
    unawaited(load());
    _connectEvents();
    _backgroundSubscription = _background.events.listen(_handleBackgroundEvent, onError: (_) {});
  }
  final ApiClient _api;
  final BackgroundDownloadService _background;
  WebSocketChannel? _channel;
  Timer? _fallback;
  StreamSubscription<BackgroundDownloadEvent>? _backgroundSubscription;

  Future<void> load() async {
    state = state.status == ResourceStatus.success ? state : const ResourceState(status: ResourceStatus.loading);
    try {
      final items = await _api.downloads();
      state = ResourceState(status: items.isEmpty ? ResourceStatus.empty : ResourceStatus.success, data: items);
    } on ApiFailure catch (failure) {
      state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message);
    }
  }

  void _connectEvents() {
    try {
      final token = _api.accessToken;
      if (token == null || token.isEmpty) {
        _startFallback();
        return;
      }
      _channel = WebSocketChannel.connect(Uri.parse(AppConfig.downloadsWebSocketUrl), headers: {'Authorization': 'Bearer $token'});
      _channel!.stream.listen(_handleEvent, onError: (_) => _startFallback(), onDone: _startFallback);
    } catch (_) {
      _startFallback();
    }
  }

  void _startFallback() {
    _fallback ??= Timer.periodic(const Duration(seconds: 5), (_) => load());
  }

  void _handleBackgroundEvent(BackgroundDownloadEvent event) => _applyEvent(event.taskId, event.event, event.progress, event.bytesDownloaded, event.totalBytes, event.outputPath, event.errorCode);

  void _handleEvent(Object? raw) {
    if (raw is! String) return;
    try {
      final json = jsonDecode(raw);
      if (json is! Map) return;
      final taskId = json['task_id'] as String?;
      if (taskId == null) return;
      _applyEvent(taskId, json['event'] as String? ?? '', int.tryParse('${json['progress_percent'] ?? json['progress'] ?? ''}'), int.tryParse('${json['bytes_downloaded'] ?? ''}'), int.tryParse('${json['total_bytes'] ?? ''}'), json['output_path'] as String?, json['error_code'] as String?);
    } catch (_) {
      _startFallback();
    }
  }

  Future<DownloadTask?> queue(AnalyzerResult analysis, MediaFormat format, {required bool authorized}) async {
    try {
      final task = await _api.createDownload(analysis, format, authorized: authorized);
      final current = [...?state.data, task];
      state = ResourceState(status: ResourceStatus.success, data: current);
      return task;
    } on ApiFailure catch (failure) {
      state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message);
      return null;
    }
  }

  Future<void> pause(String id) async => _applyTaskAction(id, _api.pauseDownload);
  Future<void> resume(String id) async => _applyTaskAction(id, _api.resumeDownload);
  Future<void> retry(String id) async => _applyTaskAction(id, _api.retryDownload);
  Future<void> open(String id) async => _applyTaskAction(id, _api.openDownload);
  Future<void> delete(String id) async {
    try {
      await _api.deleteDownload(id);
      state = ResourceState(status: ResourceStatus.success, data: [...?state.data]..removeWhere((item) => item.id == id));
    } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message); }
  }

  void _applyEvent(String taskId, String event, int? progress, int? bytes, int? total, String? outputPath, String? errorCode) {
    if (taskId.isEmpty) return;
    final current = [...?state.data];
    final index = current.indexWhere((item) => item.id == taskId);
    if (index < 0) { unawaited(load()); return; }
    final old = current[index];
    final status = switch (event) {
      'download.created' || 'created' => 'queued',
      'download.started' || 'started' => 'starting',
      'download.progress' || 'progress' => 'downloading',
      'download.completed' || 'completed' => 'completed',
      'download.failed' || 'failed' => 'failed',
      'download.cancelled' || 'cancelled' => 'cancelled',
      'download.paused' || 'paused' => 'paused',
      _ => old.status,
    };
    current[index] = DownloadTask.fromJson({...old.toJson(), 'status': status, 'progress_percent': progress ?? old.progress, 'bytes_downloaded': bytes ?? old.bytesDownloaded, 'total_bytes': total ?? old.totalBytes, 'output_path': outputPath ?? old.outputPath, 'error_code': errorCode ?? old.errorCode});
    state = ResourceState(status: ResourceStatus.success, data: current);
  }

  Future<void> _applyTaskAction(String id, Future<DownloadTask> Function(String) action) async {
    try {
      final updated = await action(id);
      final current = [...?state.data];
      final index = current.indexWhere((item) => item.id == id);
      if (index >= 0) current[index] = updated;
      state = ResourceState(status: current.isEmpty ? ResourceStatus.empty : ResourceStatus.success, data: current);
    } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message); }
  }

  Future<void> cancel(String id) async {
    try {
      final updated = await _api.cancelDownload(id);
      final current = [...?state.data];
      final index = current.indexWhere((item) => item.id == id);
      if (index >= 0) current[index] = updated;
      state = ResourceState(status: current.isEmpty ? ResourceStatus.empty : ResourceStatus.success, data: current);
    } on ApiFailure catch (failure) {
      state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message);
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _fallback?.cancel();
    _backgroundSubscription?.cancel();
    super.dispose();
  }
}

final libraryProvider = StateNotifierProvider<LibraryController, ResourceState<List<LibraryItem>>>((ref) => LibraryController(ref.read(apiClientProvider), () => ref.read(authProvider).status));
final favoritesProvider = StateNotifierProvider<CollectionController, ResourceState<List<LibraryItem>>>((ref) => CollectionController(ref.read(apiClientProvider), CollectionKind.favorites));
final historyProvider = StateNotifierProvider<CollectionController, ResourceState<List<LibraryItem>>>((ref) => CollectionController(ref.read(apiClientProvider), CollectionKind.history));

class LibraryController extends CollectionController {
  LibraryController(ApiClient api, AuthStatus Function() auth) : super(api, CollectionKind.library);
}

enum CollectionKind { library, favorites, history }

class CollectionController extends StateNotifier<ResourceState<List<LibraryItem>>> {
  CollectionController(this._api, this._kind) : super(const ResourceState()) { unawaited(load()); }
  final ApiClient _api;
  final CollectionKind _kind;
  Future<void> load() async {
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final values = switch (_kind) { CollectionKind.library => await _api.files(), CollectionKind.favorites => await _api.favorites(), CollectionKind.history => await _api.history() };
      state = ResourceState(status: values.isEmpty ? ResourceStatus.empty : ResourceStatus.success, data: values);
    } on ApiFailure catch (failure) {
      state = ResourceState(status: statusForFailure(failure), message: failure.message);
    }
  }
}

final settingsProvider = StateNotifierProvider<SettingsController, SettingsState>((ref) => SettingsController());

class SettingsState {
  const SettingsState({this.locale = 'en', this.themeMode = 'system'});
  final String locale;
  final String themeMode;
  SettingsState copyWith({String? locale, String? themeMode}) => SettingsState(locale: locale ?? this.locale, themeMode: themeMode ?? this.themeMode);
}

class SettingsController extends StateNotifier<SettingsState> {
  SettingsController() : super(const SettingsState());
  void setLocale(String value) => state = state.copyWith(locale: value);
  void setTheme(String value) => state = state.copyWith(themeMode: value);
}


final fileManagerProvider = StateNotifierProvider<FileManagerController, ResourceState<List<ManagedFile>>>((ref) => FileManagerController(ref.read(apiClientProvider)));

class FileManagerController extends StateNotifier<ResourceState<List<ManagedFile>>> {
  FileManagerController(this._api) : super(const ResourceState()) { unawaited(load()); }
  final ApiClient _api;
  String query = '';
  String sort = 'date';
  bool descending = true;

  Future<void> load({String? search, String? sortBy, bool? desc}) async {
    query = search ?? query; sort = sortBy ?? sort; descending = desc ?? descending;
    state = const ResourceState(status: ResourceStatus.loading);
    try {
      final files = await _api.files(search: query.isEmpty ? null : query, sort: sort, descending: descending);
      state = ResourceState(status: files.isEmpty ? ResourceStatus.empty : ResourceStatus.success, data: files);
    } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), message: failure.message); }
  }

  Future<void> rename(String id, String filename) async { await _apply(id, () => _api.renameFile(id, filename)); }
  Future<void> move(String id, String folder) async { await _apply(id, () => _api.moveFile(id, folder)); }
  Future<void> open(String id) async { await _apply(id, () => _api.openFile(id)); }
  Future<void> share(String id) async { await _apply(id, () => _api.shareFile(id)); }
  Future<void> favorite(String id, bool value) async {
    try {
      await _api.setFavorite(id, value);
      final files = [...?state.data];
      final index = files.indexWhere((file) => file.libraryId == id);
      if (index >= 0) files[index] = ManagedFile.fromJson({...files[index].toJson(), 'is_favorite': value});
      state = ResourceState(status: ResourceStatus.success, data: files);
    } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message); }
  }
  Future<void> delete(String id) async { try { await _api.deleteFile(id); state = ResourceState(status: ResourceStatus.success, data: [...?state.data]..removeWhere((file) => file.libraryId == id)); } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message); } }
  Future<void> _apply(String id, Future<ManagedFile> Function() action) async { try { final updated = await action(); final values = [...?state.data]; final index = values.indexWhere((file) => file.libraryId == id); if (index >= 0) values[index] = updated; state = ResourceState(status: ResourceStatus.success, data: values); } on ApiFailure catch (failure) { state = ResourceState(status: statusForFailure(failure), data: state.data, message: failure.message); } }
}

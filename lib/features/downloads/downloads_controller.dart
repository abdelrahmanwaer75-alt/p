import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../core/config/app_config.dart';
import '../../core/downloads/background_download_service.dart';
import '../../core/models/models.dart';
import '../../core/network/api_client.dart';
import '../../shared/state/resource_state.dart';
import '../auth/auth_providers.dart';

final downloadsProvider =
    StateNotifierProvider<
      DownloadsController,
      ResourceState<List<DownloadTask>>
    >((ref) {
      final controller = DownloadsController(
        ref.read(apiClientProvider),
        BackgroundDownloadService(),
      );
      ref.onDispose(controller.dispose);
      return controller;
    });

class DownloadsController
    extends StateNotifier<ResourceState<List<DownloadTask>>> {
  DownloadsController(this._api, this._background)
    : super(const ResourceState()) {
    unawaited(load());
    _connectEvents();
    _backgroundSubscription = _background.events.listen(
      _handleBackgroundEvent,
      onError: (_) {},
    );
  }

  final ApiClient _api;
  final BackgroundDownloadService _background;
  WebSocketChannel? _channel;
  Timer? _fallback;
  StreamSubscription<BackgroundDownloadEvent>? _backgroundSubscription;

  Future<void> load() async {
    state = state.status == ResourceStatus.success
        ? state
        : const ResourceState(status: ResourceStatus.loading);
    try {
      final items = await _api.downloads();
      state = ResourceState(
        status: items.isEmpty ? ResourceStatus.empty : ResourceStatus.success,
        data: items,
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  void _connectEvents() {
    try {
      final token = _api.accessToken;
      if (token == null || token.isEmpty) {
        _startFallback();
        return;
      }
      _channel = IOWebSocketChannel.connect(
        Uri.parse(AppConfig.downloadsWebSocketUrl),
        headers: {'Authorization': 'Bearer $token'},
      );
      _channel!.stream.listen(
        _handleEvent,
        onError: (_) => _startFallback(),
        onDone: _startFallback,
      );
    } catch (_) {
      _startFallback();
    }
  }

  void _startFallback() {
    _fallback ??= Timer.periodic(const Duration(seconds: 5), (_) => load());
  }

  void _handleBackgroundEvent(BackgroundDownloadEvent event) {
    // Native transfer completion is only a signal. The backend remains the
    // authority after ownership, output, and task state are verified.
    if (_isTerminalEvent(event.event)) {
      unawaited(load());
      return;
    }
    if (event.event == BackgroundDownloadEvents.notificationTap || event.open) {
      unawaited(_openAuthoritatively(event.taskId));
      return;
    }
    _applyEvent(
      event.taskId,
      event.event,
      event.progress,
      event.bytesDownloaded,
      event.totalBytes,
      event.outputPath,
      event.errorCode,
    );
  }

  Future<void> _openAuthoritatively(String taskId) async {
    if (taskId.isEmpty) return;
    try {
      await _api.openDownload(taskId);
    } on ApiFailure {
      // A notification tap must not bypass backend authorization.
    }
    await load();
  }

  void _handleEvent(Object? raw) {
    if (raw is! String) return;
    try {
      final json = jsonDecode(raw);
      if (json is! Map) return;
      final taskId = json['task_id'] as String?;
      if (taskId == null) return;
      final event = json['event'] as String? ?? '';
      if (_isTerminalEvent(event)) {
        unawaited(load());
        return;
      }
      if (event == BackgroundDownloadEvents.notificationTap ||
          json['open'] == true) {
        unawaited(_openAuthoritatively(taskId));
        return;
      }
      _applyEvent(
        taskId,
        event,
        int.tryParse('${json['progress_percent'] ?? json['progress'] ?? ''}'),
        int.tryParse('${json['bytes_downloaded'] ?? ''}'),
        int.tryParse('${json['total_bytes'] ?? ''}'),
        json['output_path'] as String?,
        json['error_code'] as String?,
      );
    } catch (_) {
      _startFallback();
    }
  }

  Future<DownloadTask?> queue(
    AnalyzerResult analysis,
    MediaFormat format, {
    required bool authorized,
  }) async {
    try {
      final task = await _api.createDownload(
        analysis,
        format,
        authorized: authorized,
      );
      final current = [...?state.data, task];
      state = ResourceState(status: ResourceStatus.success, data: current);
      return task;
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
      return null;
    }
  }

  Future<void> pause(String id) async =>
      _applyTaskAction(id, _api.pauseDownload);
  Future<void> resume(String id) async =>
      _applyTaskAction(id, _api.resumeDownload);
  Future<void> retry(String id) async =>
      _applyTaskAction(id, _api.retryDownload);
  Future<void> open(String id) async => _applyTaskAction(id, _api.openDownload);

  Future<void> delete(String id) async {
    try {
      await _api.deleteDownload(id);
      state = ResourceState(
        status: ResourceStatus.success,
        data: [...?state.data]..removeWhere((item) => item.id == id),
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  bool _isTerminalEvent(String event) =>
      event == BackgroundDownloadEvents.completed ||
      event == BackgroundDownloadEvents.failed ||
      event == BackgroundDownloadEvents.cancelled ||
      event == 'completed' ||
      event == 'failed' ||
      event == 'cancelled';

  void _applyEvent(
    String taskId,
    String event,
    int? progress,
    int? bytes,
    int? total,
    String? outputPath,
    String? errorCode,
  ) {
    if (taskId.isEmpty) return;
    final current = [...?state.data];
    final index = current.indexWhere((item) => item.id == taskId);
    if (index < 0) {
      unawaited(load());
      return;
    }
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
    current[index] = DownloadTask.fromJson({
      ...old.toJson(),
      'status': status,
      'progress_percent': progress ?? old.progress,
      'bytes_downloaded': bytes ?? old.bytesDownloaded,
      'total_bytes': total ?? old.totalBytes,
      'output_path': outputPath ?? old.outputPath,
      'error_code': errorCode ?? old.errorCode,
    });
    state = ResourceState(status: ResourceStatus.success, data: current);
  }

  Future<void> _applyTaskAction(
    String id,
    Future<DownloadTask> Function(String) action,
  ) async {
    try {
      final updated = await action(id);
      final current = [...?state.data];
      final index = current.indexWhere((item) => item.id == id);
      if (index >= 0) current[index] = updated;
      state = ResourceState(
        status: current.isEmpty ? ResourceStatus.empty : ResourceStatus.success,
        data: current,
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
    }
  }

  Future<void> cancel(String id) async {
    try {
      final updated = await _api.cancelDownload(id);
      final current = [...?state.data];
      final index = current.indexWhere((item) => item.id == id);
      if (index >= 0) current[index] = updated;
      state = ResourceState(
        status: current.isEmpty ? ResourceStatus.empty : ResourceStatus.success,
        data: current,
      );
    } on ApiFailure catch (failure) {
      state = ResourceState(
        status: statusForFailure(failure),
        data: state.data,
        message: failure.message,
      );
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

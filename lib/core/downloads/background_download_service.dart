import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BackgroundDownloadEvents {
  static const created = 'download.created';
  static const started = 'download.started';
  static const progress = 'download.progress';
  static const completed = 'download.completed';
  static const failed = 'download.failed';
  static const paused = 'download.paused';
  static const cancelled = 'download.cancelled';
  static const notificationTap = 'download.notification_tap';
}

class BackgroundDownloadEvent {
  const BackgroundDownloadEvent({
    required this.taskId,
    required this.event,
    this.progress,
    this.bytesDownloaded,
    this.totalBytes,
    this.outputPath,
    this.errorCode,
    this.sha256,
    this.open = false,
  });
  final String taskId;
  final String event;
  final int? progress;
  final int? bytesDownloaded;
  final int? totalBytes;
  final String? outputPath;
  final String? errorCode;
  final String? sha256;
  final bool open;
  factory BackgroundDownloadEvent.fromMap(Map<dynamic, dynamic> map) {
    final rawEvent =
        (map['event'] as String?) ??
        (map['open'] == true ? BackgroundDownloadEvents.notificationTap : '');
    final normalizedEvent = rawEvent.isEmpty || rawEvent.startsWith('download.')
        ? rawEvent
        : 'download.$rawEvent';
    return BackgroundDownloadEvent(
      taskId: map['task_id'] as String? ?? '',
      event: normalizedEvent,
      progress: int.tryParse(
        '${map['progress_percent'] ?? map['progress'] ?? ''}',
      ),
      bytesDownloaded: int.tryParse('${map['bytes_downloaded'] ?? ''}'),
      totalBytes: int.tryParse('${map['total_bytes'] ?? ''}'),
      outputPath: map['output_path'] as String?,
      errorCode: map['error_code'] as String?,
      sha256: map['sha256'] as String?,
      open: map['open'] == true,
    );
  }
}

class BackgroundDownloadService {
  static const _methods = MethodChannel('vidora/background_downloads');
  static const _events = EventChannel('vidora/background_download_events');
  static final BackgroundDownloadService _instance =
      BackgroundDownloadService._internal();
  factory BackgroundDownloadService() => _instance;
  BackgroundDownloadService._internal() {
    _nativeSubscription = _events
        .receiveBroadcastStream()
        .where((value) => value is Map)
        .map((value) => value as Map)
        .listen(
          (value) => _controller.add(BackgroundDownloadEvent.fromMap(value)),
        );
  }
  final StreamController<BackgroundDownloadEvent> _controller =
      StreamController<BackgroundDownloadEvent>.broadcast();
  late final StreamSubscription<dynamic> _nativeSubscription;
  Stream<BackgroundDownloadEvent> get events => _controller.stream;
  Future<bool> start({
    required String taskId,
    required String url,
    required String filename,
  }) async =>
      await _methods.invokeMethod<bool>('start', {
        'task_id': taskId,
        'url': url,
        'filename': filename,
      }) ??
      false;
  Future<bool> pause(String taskId) async =>
      await _methods.invokeMethod<bool>('pause', {'task_id': taskId}) ?? false;
  Future<bool> resume(String taskId) async =>
      await _methods.invokeMethod<bool>('resume', {'task_id': taskId}) ?? false;
  Future<bool> cancel(String taskId) async =>
      await _methods.invokeMethod<bool>('cancel', {'task_id': taskId}) ?? false;

  Future<void> dispose() async {
    await _nativeSubscription.cancel();
    await _controller.close();
  }
}

final backgroundDownloadEventsProvider =
    StreamProvider<BackgroundDownloadEvent>(
      (ref) => BackgroundDownloadService().events,
    );

import 'package:flutter_test/flutter_test.dart';
import 'package:vidora/core/downloads/background_download_service.dart';

void main() {
  test('parses worker progress_percent and byte counters', () {
    final event = BackgroundDownloadEvent.fromMap({
      'task_id': 'task-1',
      'event': 'progress',
      'progress_percent': 42,
      'bytes_downloaded': 420,
      'total_bytes': 1000,
      'sha256': 'abc123',
    });
    expect(event.event, BackgroundDownloadEvents.progress);
    expect(event.progress, 42);
    expect(event.bytesDownloaded, 420);
    expect(event.totalBytes, 1000);
    expect(event.sha256, 'abc123');
  });

  test('normalizes notification tap when native omits event name', () {
    final event = BackgroundDownloadEvent.fromMap({
      'task_id': 'task-2',
      'open': true,
    });
    expect(event.event, BackgroundDownloadEvents.notificationTap);
    expect(event.open, isTrue);
  });

  test('exposes the complete event contract', () {
    expect({
      BackgroundDownloadEvents.created,
      BackgroundDownloadEvents.started,
      BackgroundDownloadEvents.progress,
      BackgroundDownloadEvents.completed,
      BackgroundDownloadEvents.failed,
      BackgroundDownloadEvents.paused,
      BackgroundDownloadEvents.cancelled,
      BackgroundDownloadEvents.notificationTap,
    }, hasLength(8));
  });
}

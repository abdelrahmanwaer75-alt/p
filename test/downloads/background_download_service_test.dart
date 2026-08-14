import 'package:flutter_test/flutter_test.dart';

import 'package:vidora/core/downloads/background_download_service.dart';

void main() {
  test('parses native progress event', () {
    final event = BackgroundDownloadEvent.fromMap({
      'task_id': 'task-1',
      'event': 'download.progress',
      'progress': 42,
      'bytes_downloaded': 420,
      'total_bytes': 1000,
    });
    expect(event.taskId, 'task-1');
    expect(event.event, 'download.progress');
    expect(event.progress, 42);
    expect(event.bytesDownloaded, 420);
    expect(event.totalBytes, 1000);
  });

  test('parses notification tap event', () {
    final event = BackgroundDownloadEvent.fromMap({
      'task_id': 'task-2',
      'event': 'download.notification_tap',
      'open': true,
    });
    expect(event.open, isTrue);
  });
}

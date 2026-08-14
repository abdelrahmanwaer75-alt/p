import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vidora/core/models/models.dart';
import 'package:vidora/features/files/widgets/file_tile.dart';

void main() {
  testWidgets('file tile renders managed file metadata', (tester) async {
    const file = ManagedFile(
      libraryId: 'library-1',
      path: '/managed/video.mp4',
      mediaPath: '/managed/video.mp4',
      filename: 'video.mp4',
      size: 2048,
      extension: 'mp4',
      mediaType: 'video',
      title: 'Video',
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: FileTile(file: file)),
      ),
    );
    expect(find.text('video.mp4'), findsOneWidget);
    expect(find.text('mp4 • 2048 bytes'), findsOneWidget);
  });
}

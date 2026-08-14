import 'package:flutter_test/flutter_test.dart';
import 'package:media_kit/media_kit.dart';

import 'package:vidora/features/player/player_provider.dart';

void main() {
  setUpAll(MediaKit.ensureInitialized);

  test('player starts with an empty, stopped state', () {
    final controller = PlayerController();
    expect(controller.state.current, isNull);
    expect(controller.state.playing, isFalse);
    expect(controller.state.index, -1);
    controller.dispose();
  });

  test('empty playlist is rejected without changing current media', () async {
    final controller = PlayerController();
    await controller.playPlaylist(const []);
    expect(controller.state.current, isNull);
    expect(controller.state.error, contains('Playlist is empty'));
    controller.dispose();
  });

  test('invalid local path is rejected truthfully', () async {
    final controller = PlayerController();
    await controller.openFile('');
    expect(controller.state.current, isNull);
    expect(controller.state.error, contains('local file path'));
    controller.dispose();
  });
}

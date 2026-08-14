import 'package:media_kit/media_kit.dart';

/// Thin media_kit boundary. Controllers depend on this service instead of
/// importing the player engine from UI code.
class PlayerService {
  PlayerService({Player? player}) : player = player ?? Player();

  final Player player;

  Future<void> open(String path) => player.open(Media(path), play: false);
  Future<void> play() => player.play();
  Future<void> pause() => player.pause();
  Future<void> seek(Duration position) => player.seek(position);
  Future<void> setVolume(double value) => player.setVolume(value);
  Future<void> setSpeed(double value) => player.setRate(value);
  Future<void> stop() => player.stop();

  void dispose() => player.dispose();
}

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';

import '../../core/models/models.dart';

class PlayerState {
  const PlayerState({this.current, this.playing = false, this.position = Duration.zero, this.duration = Duration.zero, this.volume = 100, this.speed = 1, this.playlist = const [], this.index = -1, this.error});
  final PlaylistItem? current;
  final bool playing;
  final Duration position;
  final Duration duration;
  final double volume;
  final double speed;
  final List<PlaylistItem> playlist;
  final int index;
  final String? error;
  PlayerState copyWith({PlaylistItem? current, bool? playing, Duration? position, Duration? duration, double? volume, double? speed, List<PlaylistItem>? playlist, int? index, String? error, bool clearCurrent = false, bool clearError = false}) => PlayerState(current: clearCurrent ? null : current ?? this.current, playing: playing ?? this.playing, position: position ?? this.position, duration: duration ?? this.duration, volume: volume ?? this.volume, speed: speed ?? this.speed, playlist: playlist ?? this.playlist, index: index ?? this.index, error: clearError ? null : error ?? this.error);
}

final playerProvider = StateNotifierProvider<PlayerController, PlayerState>((ref) {
  final controller = PlayerController();
  ref.onDispose(controller.dispose);
  return controller;
});

class PlayerController extends StateNotifier<PlayerState> {
  PlayerController() : player = Player() , super(const PlayerState()) {
    _subscriptions.add(player.stream.playing.listen((value) => state = state.copyWith(playing: value)));
    _subscriptions.add(player.stream.position.listen((value) => state = state.copyWith(position: value)));
    _subscriptions.add(player.stream.duration.listen((value) => state = state.copyWith(duration: value)));
  }
  final Player player;
  final List<StreamSubscription<dynamic>> _subscriptions = [];

  Future<void> openFile(String path, {PlaylistItem? item, List<PlaylistItem>? playlist, int index = 0}) async {
    if (path.trim().isEmpty) { state = state.copyWith(error: 'A local file path is required'); return; }
    try {
      final items = playlist ?? (item == null ? const <PlaylistItem>[] : [item]);
      await player.open(Media(path), play: false);
      state = state.copyWith(current: item, playlist: items, index: items.isEmpty ? -1 : index, position: Duration.zero, duration: Duration.zero, clearError: true);
    } catch (error) { state = state.copyWith(error: 'Unable to open local media: $error'); }
  }

  Future<void> playPlaylist(List<PlaylistItem> items, {int index = 0}) async {
    if (items.isEmpty || index < 0 || index >= items.length) { state = state.copyWith(error: 'Playlist is empty'); return; }
    final item = items[index];
    if (item.mediaPath == null || item.mediaPath!.isEmpty) { state = state.copyWith(error: 'The selected playlist item has no local file'); return; }
    await openFile(item.mediaPath!, item: item, playlist: items, index: index);
    await player.play();
  }

  Future<void> play() => player.play();
  Future<void> pause() => player.pause();
  Future<void> seek(Duration position) => player.seek(position);
  Future<void> forward([Duration by = const Duration(seconds: 10)]) => player.seek(state.position + by);
  Future<void> backward([Duration by = const Duration(seconds: 10)]) => player.seek(state.position - by);
  Future<void> setVolume(double volume) async { final value = volume.clamp(0, 100).toDouble(); await player.setVolume(value); state = state.copyWith(volume: value); }
  Future<void> setSpeed(double speed) async { final value = speed.clamp(0.25, 4).toDouble(); await player.setRate(value); state = state.copyWith(speed: value); }

  Future<void> next() async { if (state.index + 1 < state.playlist.length) await playPlaylist(state.playlist, index: state.index + 1); }
  Future<void> previous() async { if (state.index > 0) await playPlaylist(state.playlist, index: state.index - 1); }
  Future<void> stop() async { await player.stop(); state = state.copyWith(clearCurrent: true, playlist: const [], index: -1, position: Duration.zero, duration: Duration.zero); }

  @override
  void dispose() { for (final subscription in _subscriptions) unawaited(subscription.cancel()); player.dispose(); super.dispose(); }
}

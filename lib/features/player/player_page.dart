import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit_video/media_kit_video.dart';

import 'player_provider.dart';

class PlayerPage extends ConsumerStatefulWidget {
  const PlayerPage({super.key});
  @override
  ConsumerState<PlayerPage> createState() => _PlayerPageState();
}

class _PlayerPageState extends ConsumerState<PlayerPage> {
  VideoController? videoController;
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    videoController ??= VideoController(
      ref.read(playerProvider.notifier).player,
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(playerProvider);
    final controller = ref.read(playerProvider.notifier);
    final isVideo = state.current?.mediaType != 'audio';
    return Scaffold(
      appBar: AppBar(title: Text(state.current?.title ?? 'Player')),
      body: state.current == null
          ? const Center(child: Text('Select a local file or playlist item'))
          : Column(
              children: [
                Expanded(
                  child: isVideo
                      ? Video(controller: videoController!)
                      : Center(
                          child: Icon(
                            Icons.audiotrack,
                            size: 96,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _progress(context, state, controller),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          IconButton(
                            onPressed: state.index > 0
                                ? controller.previous
                                : null,
                            icon: const Icon(Icons.skip_previous),
                          ),
                          IconButton(
                            onPressed: controller.backward,
                            icon: const Icon(Icons.replay_10),
                          ),
                          IconButton(
                            onPressed: state.playing
                                ? controller.pause
                                : controller.play,
                            icon: Icon(
                              state.playing
                                  ? Icons.pause_circle
                                  : Icons.play_circle,
                              size: 48,
                            ),
                          ),
                          IconButton(
                            onPressed: controller.forward,
                            icon: const Icon(Icons.forward_10),
                          ),
                          IconButton(
                            onPressed: state.index + 1 < state.playlist.length
                                ? controller.next
                                : null,
                            icon: const Icon(Icons.skip_next),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          const Icon(Icons.volume_down),
                          Expanded(
                            child: Slider(
                              value: state.volume,
                              min: 0,
                              max: 100,
                              onChanged: controller.setVolume,
                            ),
                          ),
                          DropdownButton<double>(
                            value: state.speed,
                            items: const [
                              DropdownMenuItem(value: 0.5, child: Text('0.5x')),
                              DropdownMenuItem(value: 1, child: Text('1x')),
                              DropdownMenuItem(value: 1.5, child: Text('1.5x')),
                              DropdownMenuItem(value: 2, child: Text('2x')),
                            ],
                            onChanged: (value) {
                              if (value != null) controller.setSpeed(value);
                            },
                          ),
                        ],
                      ),
                      if (state.error != null)
                        Text(
                          state.error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _progress(
    BuildContext context,
    PlayerState state,
    PlayerController controller,
  ) {
    final duration = state.duration.inMilliseconds > 0
        ? state.duration.inMilliseconds.toDouble()
        : 1.0;
    final position = state.position.inMilliseconds
        .clamp(0, duration.toInt())
        .toDouble();
    return Column(
      children: [
        Slider(
          value: position,
          min: 0,
          max: duration,
          onChanged: state.duration == Duration.zero
              ? null
              : (value) =>
                    controller.seek(Duration(milliseconds: value.round())),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(_duration(state.position)),
            Text(_duration(state.duration)),
          ],
        ),
      ],
    );
  }

  String _duration(Duration value) {
    final minutes = value.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = value.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '${value.inHours > 0 ? '${value.inHours}:' : ''}$minutes:$seconds';
  }
}

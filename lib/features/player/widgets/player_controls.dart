import 'package:flutter/material.dart';

class PlayerControls extends StatelessWidget {
  const PlayerControls({
    super.key,
    required this.playing,
    this.onPlay,
    this.onPause,
  });

  final bool playing;
  final VoidCallback? onPlay;
  final VoidCallback? onPause;

  @override
  Widget build(BuildContext context) => IconButton(
    icon: Icon(playing ? Icons.pause : Icons.play_arrow),
    onPressed: playing ? onPause : onPlay,
    tooltip: playing ? 'Pause' : 'Play',
  );
}

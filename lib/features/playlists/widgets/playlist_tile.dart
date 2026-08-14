import 'package:flutter/material.dart';

import '../../../core/models/models.dart';

class PlaylistTile extends StatelessWidget {
  const PlaylistTile({super.key, required this.playlist, this.onTap});
  final Playlist playlist;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => ListTile(
    onTap: onTap,
    title: Text(playlist.name),
    subtitle: Text('${playlist.items.length} items'),
  );
}

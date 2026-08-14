import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/models.dart';
import '../library/library_controller.dart';
import '../player/player_provider.dart';
import 'playlist_provider.dart';

class PlaylistDetailsPage extends ConsumerWidget {
  const PlaylistDetailsPage({required this.playlistId, super.key});

  final String playlistId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(playlistsProvider);
    final matches =
        state.data?.where((item) => item.id == playlistId).toList() ??
        const <Playlist>[];
    final playlist = matches.isEmpty ? null : matches.first;
    if (playlist == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Playlist')),
        body: Center(child: Text(state.message ?? 'Playlist not found')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(playlist.name),
        actions: [
          IconButton(
            onPressed: () async {
              await ref.read(playlistsProvider.notifier).play(playlist);
              if (context.mounted) context.push('/player');
            },
            icon: const Icon(Icons.play_arrow),
          ),
          IconButton(
            onPressed: () => _add(context, ref, playlist),
            icon: const Icon(Icons.add),
          ),
        ],
      ),
      body: ReorderableListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: playlist.items.length,
        onReorderItem: (oldIndex, newIndex) async {
          final items = [...playlist.items];
          final item = items.removeAt(oldIndex);
          items.insert(newIndex, item);
          await ref
              .read(playlistsProvider.notifier)
              .reorder(playlist.id, items.map((value) => value.id).toList());
        },
        itemBuilder: (_, index) {
          final item = playlist.items[index];
          return Card(
            key: ValueKey(item.id),
            child: ListTile(
              leading: const Icon(Icons.library_music),
              title: Text(item.title),
              subtitle: Text(item.mediaType),
              onTap: () async {
                await ref
                    .read(playerProvider.notifier)
                    .playPlaylist(playlist.items, index: index);
                if (context.mounted) context.push('/player');
              },
              trailing: IconButton(
                onPressed: () => ref
                    .read(playlistsProvider.notifier)
                    .removeItem(playlist.id, item.id),
                icon: const Icon(Icons.remove_circle_outline),
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _add(
    BuildContext context,
    WidgetRef ref,
    Playlist playlist,
  ) async {
    final library = ref.read(libraryProvider).data ?? const <LibraryItem>[];
    if (library.isEmpty) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No library items available')),
        );
      }
      return;
    }
    final selected = await showModalBottomSheet<LibraryItem>(
      context: context,
      builder: (context) => ListView(
        children: [
          for (final item in library)
            ListTile(
              title: Text(item.title),
              subtitle: Text(item.mediaType),
              onTap: () => Navigator.pop(context, item),
            ),
        ],
      ),
    );
    if (selected != null) {
      await ref
          .read(playlistsProvider.notifier)
          .addItem(playlist.id, selected.id);
    }
  }
}

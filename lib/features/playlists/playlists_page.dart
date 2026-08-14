import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/models.dart';
import '../../shared/state/resource_state.dart';
import '../library/library_controller.dart';
import '../player/player_provider.dart';
import 'playlist_provider.dart';

class PlaylistsPage extends ConsumerWidget {
  const PlaylistsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(playlistsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Playlists'),
        actions: [
          IconButton(
            onPressed: () => _create(context, ref),
            icon: const Icon(Icons.add),
          ),
        ],
      ),
      body: switch (state.status) {
        ResourceStatus.loading => const Center(
          child: CircularProgressIndicator(),
        ),
        ResourceStatus.empty => Center(
          child: FilledButton.icon(
            onPressed: () => _create(context, ref),
            icon: const Icon(Icons.add),
            label: const Text('Create playlist'),
          ),
        ),
        ResourceStatus.error ||
        ResourceStatus.offline ||
        ResourceStatus.unauthorized => Center(
          child: Text(state.message ?? 'Unable to load playlists'),
        ),
        _ => ListView.separated(
          padding: const EdgeInsets.all(12),
          itemCount: state.data?.length ?? 0,
          separatorBuilder: (_, _) => const SizedBox(height: 8),
          itemBuilder: (_, index) {
            final playlist = state.data![index];
            return Card(
              child: ListTile(
                leading: const Icon(Icons.queue_music),
                title: Text(playlist.name),
                subtitle: Text('${playlist.items.length} items'),
                onTap: () => context.push('/playlists/${playlist.id}'),
                trailing: PopupMenuButton<String>(
                  onSelected: (action) async {
                    if (action == 'delete') {
                      await ref
                          .read(playlistsProvider.notifier)
                          .delete(playlist.id);
                    }
                    if (action == 'rename') {
                      if (!context.mounted) return;
                      await _rename(context, ref, playlist);
                    }
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(value: 'rename', child: Text('Rename')),
                    PopupMenuItem(value: 'delete', child: Text('Delete')),
                  ],
                ),
              ),
            );
          },
        ),
      },
    );
  }

  static Future<void> _create(BuildContext context, WidgetRef ref) async {
    final name = await _nameDialog(context, 'Create playlist', '');
    if (name != null && name.trim().isNotEmpty) {
      await ref.read(playlistsProvider.notifier).create(name.trim());
    }
  }

  static Future<void> _rename(
    BuildContext context,
    WidgetRef ref,
    Playlist playlist,
  ) async {
    final name = await _nameDialog(context, 'Rename playlist', playlist.name);
    if (name != null && name.trim().isNotEmpty) {
      await ref
          .read(playlistsProvider.notifier)
          .update(playlist.id, name: name.trim());
    }
  }

  static Future<String?> _nameDialog(
    BuildContext context,
    String title,
    String initial,
  ) async {
    final controller = TextEditingController(text: initial);
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(controller: controller, autofocus: true),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();
    return result;
  }
}

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

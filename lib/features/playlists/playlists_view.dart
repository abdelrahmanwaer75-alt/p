import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/models.dart';
import '../../shared/state/resource_state.dart';
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

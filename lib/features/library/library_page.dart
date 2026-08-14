import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../shared/state/resource_state.dart';
import '../files/files_controller.dart';

class LibraryPage extends ConsumerStatefulWidget {
  const LibraryPage({super.key});

  @override
  ConsumerState<LibraryPage> createState() => _LibraryPageState();
}

class _LibraryPageState extends ConsumerState<LibraryPage> {
  final search = TextEditingController();

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(fileManagerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Library'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) =>
                ref.read(fileManagerProvider.notifier).load(sortBy: value),
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'name', child: Text('Sort by name')),
              PopupMenuItem(value: 'size', child: Text('Sort by size')),
              PopupMenuItem(value: 'date', child: Text('Sort by date')),
              PopupMenuItem(value: 'type', child: Text('Sort by type')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: search,
              onSubmitted: (value) =>
                  ref.read(fileManagerProvider.notifier).load(search: value),
              decoration: InputDecoration(
                labelText: 'Search files',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    search.clear();
                    ref.read(fileManagerProvider.notifier).load(search: '');
                  },
                ),
              ),
            ),
          ),
          Expanded(child: _body(context, state)),
        ],
      ),
    );
  }

  Widget _body(BuildContext context, ResourceState<List<ManagedFile>> state) {
    switch (state.status) {
      case ResourceStatus.loading:
        return const Center(child: CircularProgressIndicator());
      case ResourceStatus.empty:
        return const Center(child: Text('No files'));
      case ResourceStatus.error:
      case ResourceStatus.offline:
      case ResourceStatus.unauthorized:
        return Center(child: Text(state.message ?? 'Unable to load files'));
      case ResourceStatus.idle:
        return const SizedBox.shrink();
      case ResourceStatus.success:
        final files = state.data ?? const <ManagedFile>[];
        return RefreshIndicator(
          onRefresh: () => ref.read(fileManagerProvider.notifier).load(),
          child: ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: files.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (_, index) => _fileCard(files[index]),
          ),
        );
    }
  }

  Widget _fileCard(ManagedFile file) => Card(
    child: ListTile(
      leading: Icon(
        file.mediaType == 'audio' ? Icons.audiotrack : Icons.video_file,
      ),
      title: Text(file.filename),
      subtitle: Text('${file.size} bytes · ${file.extension}\n${file.title}'),
      isThreeLine: true,
      trailing: PopupMenuButton<String>(
        onSelected: (action) => _action(file, action),
        itemBuilder: (_) => [
          const PopupMenuItem(value: 'open', child: Text('Open')),
          const PopupMenuItem(value: 'share', child: Text('Share')),
          const PopupMenuItem(value: 'rename', child: Text('Rename')),
          const PopupMenuItem(value: 'move', child: Text('Move')),
          PopupMenuItem(
            value: 'favorite',
            child: Text(file.isFavorite ? 'Unfavorite' : 'Favorite'),
          ),
          const PopupMenuItem(value: 'delete', child: Text('Delete')),
        ],
      ),
    ),
  );

  Future<void> _action(ManagedFile file, String action) async {
    final provider = ref.read(fileManagerProvider.notifier);
    switch (action) {
      case 'open':
        await provider.open(file.libraryId);
      case 'share':
        await provider.share(file.libraryId);
      case 'rename':
        final name = await _textDialog('Rename', file.filename);
        if (name != null) await provider.rename(file.libraryId, name);
      case 'move':
        final folder = await _textDialog('Move to folder', '');
        if (folder != null) await provider.move(file.libraryId, folder);
      case 'favorite':
        await provider.favorite(file.libraryId, !file.isFavorite);
      case 'delete':
        await provider.delete(file.libraryId);
    }
  }

  Future<String?> _textDialog(String title, String initial) async {
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

class CollectionView extends StatelessWidget {
  const CollectionView({
    required this.title,
    required this.state,
    required this.reload,
    super.key,
  });

  final String title;
  final ResourceState<List<dynamic>> state;
  final Future<void> Function() reload;

  @override
  Widget build(BuildContext context) {
    if (state.status == ResourceStatus.loading) {
      return Scaffold(
        appBar: AppBar(title: Text(title)),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (state.status == ResourceStatus.error ||
        state.status == ResourceStatus.offline ||
        state.status == ResourceStatus.unauthorized) {
      return Scaffold(
        appBar: AppBar(title: Text(title)),
        body: Center(child: Text(state.message ?? 'Unable to load $title')),
      );
    }
    final items = state.data ?? const [];
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: state.status == ResourceStatus.empty
          ? Center(child: Text('$title is empty'))
          : RefreshIndicator(
              onRefresh: reload,
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: items.length,
                separatorBuilder: (_, _) => const SizedBox(height: 8),
                itemBuilder: (_, index) {
                  final item = items[index];
                  return Card(
                    child: ListTile(
                      leading: const Icon(Icons.folder_rounded),
                      title: Text(item.title),
                      subtitle: Text(item.sourceUrl),
                    ),
                  );
                },
              ),
            ),
    );
  }
}

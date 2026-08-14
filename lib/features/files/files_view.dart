import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/state/resource_state.dart';
import 'files_controller.dart';
import 'widgets/file_tile.dart';

class FilesView extends ConsumerStatefulWidget {
  const FilesView({super.key});

  @override
  ConsumerState<FilesView> createState() => _FilesViewState();
}

class _FilesViewState extends ConsumerState<FilesView> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(fileManagerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Files')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _search,
              decoration: const InputDecoration(labelText: 'Search files'),
              onSubmitted: (value) =>
                  ref.read(fileManagerProvider.notifier).load(search: value),
            ),
          ),
          Expanded(child: _FilesBody(state: state)),
        ],
      ),
    );
  }
}

class _FilesBody extends ConsumerWidget {
  const _FilesBody({required this.state});
  final ResourceState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (state.status == ResourceStatus.loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.status == ResourceStatus.error ||
        state.status == ResourceStatus.unauthorized ||
        state.status == ResourceStatus.offline) {
      return Center(child: Text(state.message ?? 'Unable to load files'));
    }
    final files = (state.data as List?)?.cast<dynamic>() ?? const [];
    if (files.isEmpty) return const Center(child: Text('No files'));
    return ListView.builder(
      itemCount: files.length,
      itemBuilder: (_, index) => FileTile(file: files[index]),
    );
  }
}

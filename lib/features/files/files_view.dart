import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_localizations.dart';
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
    final strings = AppLocalizations.of(context);
    final state = ref.watch(fileManagerProvider);
    return Scaffold(
      appBar: AppBar(title: Text(strings.files)),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _search,
              decoration: InputDecoration(labelText: strings.searchFiles),
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
    final strings = AppLocalizations.of(context);
    if (state.status == ResourceStatus.loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.status == ResourceStatus.error ||
        state.status == ResourceStatus.unauthorized ||
        state.status == ResourceStatus.offline) {
      final fallback = switch (state.status) {
        ResourceStatus.unauthorized =>
          strings.isArabic ? 'يلزم تسجيل الدخول' : 'Authentication required',
        ResourceStatus.offline =>
          strings.isArabic
              ? 'لا يوجد اتصال بالشبكة'
              : 'You appear to be offline',
        _ => '${strings.unableToLoad} ${strings.files.toLowerCase()}',
      };
      return Center(child: Text(state.message ?? fallback));
    }
    final files = (state.data as List?)?.cast<dynamic>() ?? const [];
    if (files.isEmpty) {
      return Center(child: Text(strings.noFiles));
    }
    return ListView.builder(
      itemCount: files.length,
      itemBuilder: (_, index) => FileTile(file: files[index]),
    );
  }
}

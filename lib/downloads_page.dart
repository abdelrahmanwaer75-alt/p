import 'package:flutter/material.dart';

import 'core_api.dart';

class DownloadsPage extends StatefulWidget {
  final VidoraApiClient api;
  final String title;
  final String emptyTitle;
  final String emptyBody;
  const DownloadsPage({
    super.key,
    required this.api,
    required this.title,
    required this.emptyTitle,
    required this.emptyBody,
  });

  @override
  State<DownloadsPage> createState() => _DownloadsPageState();
}

class _DownloadsPageState extends State<DownloadsPage> {
  late Future<List<DownloadTask>> future;

  @override
  void initState() {
    super.initState();
    future = widget.api.downloads();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: FutureBuilder<List<DownloadTask>>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError || (snapshot.data ?? const []).isEmpty) {
          return _empty();
        }
        final tasks = snapshot.data!;
        return RefreshIndicator(
          onRefresh: () async {
            setState(() {
              future = widget.api.downloads();
            });
            await future;
          },
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: tasks.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, index) => _taskCard(tasks[index]),
          ),
        );
      },
    ),
  );

  Widget _empty() => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.download_rounded, size: 48),
          const SizedBox(height: 16),
          Text(widget.emptyTitle),
          const SizedBox(height: 8),
          Text(widget.emptyBody, textAlign: TextAlign.center),
        ],
      ),
    ),
  );

  Widget _taskCard(DownloadTask task) {
    final progress = task.progressKnown && task.progressPercent != null
        ? '${task.progressPercent!.toStringAsFixed(0)}%'
        : 'Progress unavailable';
    return Card(
      child: ListTile(
        leading: Icon(_statusIcon(task.status)),
        title: Text(task.formatId),
        subtitle: Text('${task.status} · $progress\n${task.sourceUrl}'),
        isThreeLine: true,
      ),
    );
  }

  IconData _statusIcon(String status) => switch (status) {
    'completed' => Icons.check_circle_rounded,
    'failed' => Icons.error_rounded,
    'running' => Icons.downloading_rounded,
    _ => Icons.schedule_rounded,
  };
}

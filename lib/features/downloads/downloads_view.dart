import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/localization/app_localizations.dart';
import '../../core/models/models.dart';
import '../../shared/state/resource_state.dart';
import 'downloads_controller.dart';

class DownloadsPage extends ConsumerWidget {
  const DownloadsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = AppLocalizations.of(context);
    final state = ref.watch(downloadsProvider);
    if (state.status == ResourceStatus.loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (state.status == ResourceStatus.error ||
        state.status == ResourceStatus.offline ||
        state.status == ResourceStatus.unauthorized) {
      return Scaffold(
        appBar: AppBar(title: Text(strings.downloads)),
        body: Center(
          child: Text(state.message ?? strings.unableToLoadDownloads),
        ),
      );
    }
    final tasks = state.data ?? const <DownloadTask>[];
    if (state.status == ResourceStatus.empty) {
      return Scaffold(body: Center(child: Text(strings.noDownloads)));
    }
    final groups = <String, List<DownloadTask>>{
      strings.active: tasks
          .where(
            (task) =>
                {'starting', 'downloading', 'paused'}.contains(task.status),
          )
          .toList(),
      strings.queued: tasks.where((task) => task.status == 'queued').toList(),
      strings.completed: tasks
          .where((task) => task.status == 'completed')
          .toList(),
      strings.failed: tasks.where((task) => task.status == 'failed').toList(),
      strings.cancelled: tasks
          .where((task) => task.status == 'cancelled')
          .toList(),
    };
    return Scaffold(
      appBar: AppBar(title: Text(strings.downloads)),
      body: RefreshIndicator(
        onRefresh: () => ref.read(downloadsProvider.notifier).load(),
        child: ListView(
          padding: const EdgeInsets.all(12),
          children: [
            for (final entry in groups.entries)
              if (entry.value.isNotEmpty) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 12, bottom: 8),
                  child: Text(
                    entry.key,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                for (final task in entry.value) _taskCard(context, ref, task),
              ],
          ],
        ),
      ),
    );
  }

  Widget _taskCard(BuildContext context, WidgetRef ref, DownloadTask task) {
    final strings = AppLocalizations.of(context);
    final known = task.progress != null;
    final progress = known ? task.progress!.clamp(0, 100) / 100 : null;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (task.thumbnail != null)
                  const Icon(Icons.image_outlined)
                else
                  const Icon(Icons.video_file),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    task.title ?? task.formatId,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
                _actions(context, ref, task),
              ],
            ),
            const SizedBox(height: 8),
            Text(task.status),
            if (progress != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: LinearProgressIndicator(value: progress.toDouble()),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${known ? '${task.progress!.toStringAsFixed(0)}%' : strings.progressUnavailable} · ${_bytes(task.bytesDownloaded)} / ${task.totalBytes == null ? '—' : _bytes(task.totalBytes!)}',
                ),
                Text(
                  task.speed == null
                      ? '—'
                      : '${_bytes(task.speed!.round())}/s · ETA ${task.eta ?? '—'}s',
                ),
              ],
            ),
            if (task.errorMessage != null)
              Text(
                task.errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
          ],
        ),
      ),
    );
  }

  Widget _actions(BuildContext context, WidgetRef ref, DownloadTask task) {
    final actions = <String>[];
    switch (task.status) {
      case 'queued':
      case 'starting':
      case 'downloading':
        actions.addAll(['pause', 'cancel']);
      case 'paused':
        actions.addAll(['resume', 'cancel']);
      case 'completed':
        actions.addAll(['open', 'delete']);
      case 'failed':
        actions.addAll(['retry', 'delete']);
      case 'cancelled':
        actions.add('delete');
    }
    return PopupMenuButton<String>(
      onSelected: (action) async {
        final controller = ref.read(downloadsProvider.notifier);
        switch (action) {
          case 'pause':
            await controller.pause(task.id);
          case 'resume':
            await controller.resume(task.id);
          case 'cancel':
            await controller.cancel(task.id);
          case 'retry':
            await controller.retry(task.id);
          case 'open':
            await controller.open(task.id);
          case 'delete':
            await controller.delete(task.id);
        }
      },
      itemBuilder: (_) {
        final strings = AppLocalizations.of(context);
        final labels = <String, String>{
          'pause': strings.pause,
          'resume': strings.resume,
          'cancel': strings.cancel,
          'retry': strings.retry,
          'open': strings.open,
          'delete': strings.delete,
        };
        return [
          for (final action in actions)
            PopupMenuItem(
              value: action,
              child: Text(labels[action] ?? action),
            ),
        ];
      },
    );
  }

  String _bytes(int value) {
    if (value < 1024) return '$value B';
    if (value < 1024 * 1024) return '${(value / 1024).toStringAsFixed(1)} KB';
    if (value < 1024 * 1024 * 1024) {
      return '${(value / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(value / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }
}

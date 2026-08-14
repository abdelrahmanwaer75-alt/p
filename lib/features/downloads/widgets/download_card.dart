import 'package:flutter/material.dart';

import '../../../core/models/models.dart';

/// Presentational summary for a download task. It does not initiate network work.
class DownloadCard extends StatelessWidget {
  const DownloadCard({super.key, required this.task, this.onTap});

  final DownloadTask task;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,
      title: Text(task.title ?? task.sourceUrl),
      subtitle: Text(task.status),
      trailing: task.progress == null
          ? null
          : SizedBox(
              width: 72,
              child: LinearProgressIndicator(value: task.progress),
            ),
    );
  }
}

import 'package:flutter/material.dart';

class DownloadEmptyState extends StatelessWidget {
  const DownloadEmptyState({super.key, this.message = 'No downloads'});

  final String message;

  @override
  Widget build(BuildContext context) => Center(child: Text(message));
}

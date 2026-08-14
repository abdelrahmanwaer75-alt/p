import 'package:flutter/material.dart';

/// Renders only worker-reported progress; null means indeterminate/unknown.
class DownloadProgress extends StatelessWidget {
  const DownloadProgress({super.key, required this.value});

  final double? value;

  @override
  Widget build(BuildContext context) => LinearProgressIndicator(value: value);
}

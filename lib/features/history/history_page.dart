import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../library/library_page.dart';
import '../providers.dart';

class HistoryPage extends ConsumerWidget {
  const HistoryPage({super.key});
  @override Widget build(BuildContext context, WidgetRef ref) => CollectionView(title: 'History', state: ref.watch(historyProvider), reload: () => ref.read(historyProvider.notifier).load());
}

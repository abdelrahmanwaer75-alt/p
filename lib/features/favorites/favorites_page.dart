import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../library/library_page.dart';
import '../providers.dart';

class FavoritesPage extends ConsumerWidget {
  const FavoritesPage({super.key});
  @override Widget build(BuildContext context, WidgetRef ref) => CollectionView(title: 'Favorites', state: ref.watch(favoritesProvider), reload: () => ref.read(favoritesProvider.notifier).load());
}

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/localization/app_localizations.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final strings = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(strings.appTitle)),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(
            strings.goodEvening,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(strings.homeDescription),
          const SizedBox(height: 28),
          FilledButton.icon(
            onPressed: () => context.go('/analyze'),
            icon: const Icon(Icons.search_rounded),
            label: Text(strings.analyze),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => context.go('/playlists'),
            icon: const Icon(Icons.queue_music),
            label: Text(strings.playlists),
          ),
        ],
      ),
    );
  }
}

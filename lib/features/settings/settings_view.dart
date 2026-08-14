import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/localization/app_localizations.dart';
import '../auth/auth_providers.dart';
import 'settings_controller.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final strings = AppLocalizations.of(context);
    final settings = ref.watch(settingsProvider);
    final auth = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(title: Text(strings.settings)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ListTile(
            title: Text(auth.session?.user.email ?? 'Account'),
            subtitle: Text(
              strings.isArabic ? 'جلسة موثقة' : 'Authenticated session',
            ),
          ),
          const Divider(),
          ListTile(title: Text(strings.appearance)),
          DropdownButtonFormField<String>(
            initialValue: settings.themeMode,
            decoration: InputDecoration(labelText: strings.theme),
            items: [
              DropdownMenuItem(value: 'system', child: Text(strings.system)),
              DropdownMenuItem(value: 'light', child: Text(strings.light)),
              DropdownMenuItem(value: 'dark', child: Text(strings.dark)),
            ],
            onChanged: (value) {
              if (value != null) {
                ref.read(settingsProvider.notifier).setTheme(value);
              }
            },
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            initialValue: settings.locale,
            decoration: InputDecoration(labelText: strings.language),
            items: [
              DropdownMenuItem(value: 'en', child: Text(strings.english)),
              DropdownMenuItem(value: 'ar', child: Text(strings.arabic)),
            ],
            onChanged: (value) {
              if (value != null) {
                ref.read(settingsProvider.notifier).setLocale(value);
              }
            },
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () async {
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
            icon: const Icon(Icons.logout),
            label: Text(strings.signOut),
          ),
        ],
      ),
    );
  }
}

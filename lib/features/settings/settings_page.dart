import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../auth/auth_providers.dart';
import '../providers.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});
  @override Widget build(BuildContext context, WidgetRef ref) { final settings = ref.watch(settingsProvider); final auth = ref.watch(authProvider); return Scaffold(appBar: AppBar(title: const Text('Settings')), body: ListView(padding: const EdgeInsets.all(16), children: [ListTile(title: Text(auth.session?.user.email ?? 'Account'), subtitle: const Text('Authenticated session')), const Divider(), const ListTile(title: Text('Appearance')), DropdownButtonFormField<String>(initialValue: settings.themeMode, decoration: const InputDecoration(labelText: 'Theme'), items: const [DropdownMenuItem(value: 'system', child: Text('System')), DropdownMenuItem(value: 'light', child: Text('Light')), DropdownMenuItem(value: 'dark', child: Text('Dark'))], onChanged: (value) { if (value != null) ref.read(settingsProvider.notifier).setTheme(value); }), const SizedBox(height: 16), DropdownButtonFormField<String>(initialValue: settings.locale, decoration: const InputDecoration(labelText: 'Language'), items: const [DropdownMenuItem(value: 'en', child: Text('English')), DropdownMenuItem(value: 'ar', child: Text('العربية'))], onChanged: (value) { if (value != null) ref.read(settingsProvider.notifier).setLocale(value); }), const SizedBox(height: 24), OutlinedButton.icon(onPressed: () async { await ref.read(authProvider.notifier).logout(); if (context.mounted) context.go('/login'); }, icon: const Icon(Icons.logout), label: const Text('Sign out'))])); }
}

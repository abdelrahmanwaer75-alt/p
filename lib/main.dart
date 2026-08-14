import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'features/providers.dart';
import 'routing/app_router.dart';

void main() => runApp(const ProviderScope(child: VidoraApp()));

class VidoraApp extends ConsumerWidget {
  const VidoraApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final themeMode = switch (settings.themeMode) { 'light' => ThemeMode.light, 'dark' => ThemeMode.dark, _ => ThemeMode.system };
    const seed = Color(0xFF6750A4);
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Vidora',
      routerConfig: ref.watch(routerProvider),
      themeMode: themeMode,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: seed), useMaterial3: true, fontFamily: 'Roboto'),
      darkTheme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: seed, brightness: Brightness.dark), useMaterial3: true, fontFamily: 'Roboto'),
      locale: Locale(settings.locale),
    );
  }
}

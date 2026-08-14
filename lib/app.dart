import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/downloads/background_download_service.dart';
import 'core/theme/app_theme.dart';
import 'features/providers.dart';
import 'navigation/app_router.dart';

class VidoraApp extends ConsumerWidget {
  const VidoraApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.listen<AsyncValue<BackgroundDownloadEvent>>(
      backgroundDownloadEventsProvider,
      (_, next) {
        final event = next.valueOrNull;
        if (event?.open == true) {
          ref.read(routerProvider).go('/downloads');
        }
      },
    );

    final settings = ref.watch(settingsProvider);
    final themeMode = switch (settings.themeMode) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Vidora',
      routerConfig: ref.watch(routerProvider),
      themeMode: themeMode,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      locale: Locale(settings.locale),
    );
  }
}

import 'package:flutter_riverpod/flutter_riverpod.dart';

final settingsProvider =
    StateNotifierProvider<SettingsController, SettingsState>(
      (ref) => SettingsController(),
    );

class SettingsState {
  const SettingsState({this.locale = 'en', this.themeMode = 'system'});

  final String locale;
  final String themeMode;

  SettingsState copyWith({String? locale, String? themeMode}) => SettingsState(
    locale: locale ?? this.locale,
    themeMode: themeMode ?? this.themeMode,
  );
}

class SettingsController extends StateNotifier<SettingsState> {
  SettingsController() : super(const SettingsState());

  void setLocale(String value) => state = state.copyWith(locale: value);
  void setTheme(String value) => state = state.copyWith(themeMode: value);
}

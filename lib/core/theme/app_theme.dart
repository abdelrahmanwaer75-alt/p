import 'package:flutter/material.dart';

class AppTheme {
  const AppTheme._();

  static const seedColor = Color(0xFF6750A4);

  static ThemeData light() => ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: seedColor),
    useMaterial3: true,
    fontFamily: 'Roboto',
  );

  static ThemeData dark() => ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: seedColor,
      brightness: Brightness.dark,
    ),
    useMaterial3: true,
    fontFamily: 'Roboto',
  );
}

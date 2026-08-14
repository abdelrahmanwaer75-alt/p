import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vidora/core/localization/app_localizations.dart';

void main() {
  testWidgets('English localization uses LTR labels', (tester) async {
    TextDirection? direction;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('en'),
        supportedLocales: const [Locale('en'), Locale('ar')],
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Builder(
          builder: (context) {
            direction = Directionality.of(context);
            return Text(AppLocalizations.of(context).home);
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Home'), findsOneWidget);
    expect(direction, TextDirection.ltr);
  });

  testWidgets('Arabic localization uses Arabic labels and RTL direction', (
    tester,
  ) async {
    TextDirection? direction;
    await tester.pumpWidget(
      MaterialApp(
        locale: const Locale('ar'),
        supportedLocales: const [Locale('en'), Locale('ar')],
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: Builder(
          builder: (context) {
            direction = Directionality.of(context);
            return Text(AppLocalizations.of(context).home);
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('الرئيسية'), findsOneWidget);
    expect(direction, TextDirection.rtl);
  });
}

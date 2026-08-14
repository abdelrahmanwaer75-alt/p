import 'package:flutter_test/flutter_test.dart';

import 'package:vidora/main.dart';

void main() {
  testWidgets('Vidora onboarding starts correctly', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const VidoraApp());
    expect(find.text('Vidora'), findsOneWidget);
    expect(find.text('Download. Organize. Enjoy.'), findsOneWidget);
    expect(find.text('Get started'), findsOneWidget);

    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();
    expect(find.text('Good evening'), findsOneWidget);
    expect(find.text('Downloads'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
  });
}

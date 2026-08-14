import 'package:flutter_test/flutter_test.dart';

import 'package:vidora/main.dart';

void main() {
  testWidgets('Vidora starts at onboarding and routes to sign in', (WidgetTester tester) async {
    await tester.pumpWidget(const VidoraApp());
    await tester.pumpAndSettle();
    expect(find.text('Vidora'), findsOneWidget);
    expect(find.text('Download and organize authorized media.'), findsOneWidget);
    expect(find.text('Get started'), findsOneWidget);

    await tester.tap(find.text('Get started'));
    await tester.pumpAndSettle();
    expect(find.text('Sign in'), findsOneWidget);
  });
}

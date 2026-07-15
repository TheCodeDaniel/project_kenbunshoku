import 'package:flutter_test/flutter_test.dart';

import 'package:kenbunshoku_notify/main.dart';

void main() {
  testWidgets('app starts on the alert feed with an empty state', (WidgetTester tester) async {
    await tester.pumpWidget(const KenbunshokuNotifyApp());
    await tester.pump();

    expect(find.text('Kenbunshoku Alerts'), findsOneWidget);
    expect(find.textContaining('No alerts yet'), findsOneWidget);
  });
}

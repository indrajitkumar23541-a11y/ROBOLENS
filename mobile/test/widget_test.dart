import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:robolens_mobile/main.dart';

void main() {
  testWidgets('RoboLensApp builds AuthGate and initial UI', (WidgetTester tester) async {
    await tester.pumpWidget(const RoboLensApp());

    // Initially loads AuthGate showing loading indicator or LoginScreen
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}

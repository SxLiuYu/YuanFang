// This is a basic widget test for the HomeAssistantApp.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:openclaw_home_assistant/main.dart';

void main() {
  testWidgets('HomeAssistantApp renders correctly', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const HomeAssistantApp());

    // Verify that the app title is present
    expect(find.text('OpenClaw Home Assistant'), findsOneWidget);
    
    // Verify that the status text is present
    expect(find.text('Status:'), findsOneWidget);
  });
}
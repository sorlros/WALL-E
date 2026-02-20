import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:frontend/main.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Login Flow Test', (WidgetTester tester) async {
    // Load .env for test
    await dotenv.load(fileName: ".env");

    // Launch App
    await tester.pumpWidget(const WallEApp());
    await tester.pumpAndSettle();

    // Verify Login Screen
    expect(find.text('Wall-E'), findsOneWidget);
    expect(find.text('로그인'), findsOneWidget);

    // Enter Credentials
    await tester.enterText(find.byType(TextField).at(0), 'test@example.com');
    await tester.enterText(find.byType(TextField).at(1), 'password123');
    await tester.pump();

    // Tap Login
    await tester.tap(find.text('로그인'));
    await tester.pump();

    // Wait for network (timeout simulation)
    print("Login tapped. Waiting for response...");
    await Future.delayed(const Duration(seconds: 2));
    await tester.pumpAndSettle();
  });
}

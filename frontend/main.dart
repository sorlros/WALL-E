import 'package:flutter/material.dart';

import 'screens/new_mission_screen.dart';
import 'screens/live_feed_screen.dart';
import 'screens/analysis_report_screen.dart';
import 'screens/export_report_screen.dart';

void main() {
  runApp(const DroneCrackApp());
}

class DroneCrackApp extends StatelessWidget {
  const DroneCrackApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Drone Crack App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
      ),
      initialRoute: NewMissionScreen.routeName,
      routes: {
        NewMissionScreen.routeName: (_) => const NewMissionScreen(),
        LiveFeedScreen.routeName: (_) => const LiveFeedScreen(),
        AnalysisReportScreen.routeName: (_) => const AnalysisReportScreen(),
        ExportReportScreen.routeName: (_) => const ExportReportScreen(),
      },
    );
  }
}
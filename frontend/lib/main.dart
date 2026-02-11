import 'package:flutter/material.dart';
import 'screens/new_mission_screen.dart';
import 'screens/gallery_screen.dart';
import 'screens/live_streaming_screen.dart';

void main() {
  runApp(const WallEApp());
}

class WallEApp extends StatelessWidget {
  const WallEApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Wall-E Drone Inspection',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF101622),
        fontFamily: 'Noto Sans KR',
      ),
      home: const MainNavigator(),
    );
  }
}

class MainNavigator extends StatefulWidget {
  const MainNavigator({super.key});

  @override
  State<MainNavigator> createState() => _MainNavigatorState();
}

class _MainNavigatorState extends State<MainNavigator> {
  int _currentIndex = 1; // Start with New Mission (Middle Tab)

  final List<Widget> _screens = [
    const LiveStreamingScreen(), // Index 0: Live Stream
    const NewMissionScreen(), // Index 1: Home / New Mission
    const GalleryScreen(), // Index 2: Gallery
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        backgroundColor: const Color(0xFF101622),
        selectedItemColor: const Color(0xFF135BEC),
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.videocam),
            label: '실시간 영상',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.add_circle_outline),
            label: '새 미션',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.grid_view),
            label: '라이브러리', // Gallery
          ),
        ],
      ),
    );
  }
}

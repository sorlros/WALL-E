import 'package:flutter/material.dart';
import 'screens/new_mission_screen.dart';
import 'screens/gallery_screen.dart';
import 'screens/login_screen.dart';
import 'screens/profile_screen.dart';
import 'services/api_service.dart';

import 'package:flutter_dotenv/flutter_dotenv.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  await ApiService.init(); // Initialize SharedPrefs
  runApp(const WallEApp());
}

class WallEApp extends StatelessWidget {
  const WallEApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Wall-E Drone Inspection',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF101622),
        fontFamily: 'Noto Sans KR',
      ),
      home: const LoginScreen(), // Set directly to LoginScreen
    );
  }
}

class MainNavigator extends StatefulWidget {
  const MainNavigator({super.key});

  @override
  State<MainNavigator> createState() => _MainNavigatorState();
}

class _MainNavigatorState extends State<MainNavigator> {
  int _currentIndex = 0; // Start with New Mission (First Tab)

  final List<Widget> _screens = [
    const NewMissionScreen(), // Index 0: New Mission (was 1)
    const GalleryScreen(), // Index 1: Gallery (was 2)
    const ProfileScreen(), // Index 2: Profile
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
            icon: Icon(Icons.add_circle_outline),
            label: '새 미션',
          ),
          BottomNavigationBarItem(icon: Icon(Icons.grid_view), label: '라이브러리'),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            label: '프로필',
          ),
        ],
      ),
    );
  }
}

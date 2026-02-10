import 'package:flutter/material.dart';
import 'analysis_report_screen.dart';

class LiveFeedScreen extends StatelessWidget {
  static const routeName = '/live-feed';
  const LiveFeedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          Positioned.fill(
            child: Image.network(
              'https://images.unsplash.com/photo-1590060419128-296b3400c65a?auto=format&fit=crop&q=80&w=1000',
              fit: BoxFit.cover,
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.battery_std,
                            color: Colors.orange, size: 18),
                        Text(' 85%',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(width: 12),
                        Icon(Icons.signal_cellular_alt,
                            color: Colors.orange, size: 18),
                        Text(' STRONG',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(width: 12),
                        Icon(Icons.access_time,
                            color: Colors.orange, size: 18),
                        Text(' 12:45:08',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            top: 200,
            left: 100,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  color: Colors.orange,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  child: const Text(
                    'SURFACE CRACK: 92%',
                    style: TextStyle(color: Colors.white, fontSize: 10),
                  ),
                ),
                Container(
                  width: 150,
                  height: 120,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.orange, width: 2),
                  ),
                ),
              ],
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              color: Colors.black54,
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _NavIcon(
                    icon: Icons.videocam,
                    label: "LIVE FEED",
                    active: true,
                    onTap: () {},
                  ),
                  _NavIcon(
                    icon: Icons.assignment,
                    label: "REPORTS",
                    active: false,
                    onTap: () {
                      Navigator.pushNamed(
                          context, AnalysisReportScreen.routeName);
                    },
                  ),
                  _NavIcon(
                    icon: Icons.settings,
                    label: "SETTINGS",
                    active: false,
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Settings (TODO)')),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NavIcon extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _NavIcon({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = active ? Colors.orange : Colors.white70;

    return InkWell(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color),
          Text(label, style: TextStyle(color: color, fontSize: 10)),
        ],
      ),
    );
  }
}
import 'package:flutter/material.dart';

// ==========================================
// 🌟 Option C: Drone Camera Calibration UI
// ==========================================
class OptionCLoading extends StatefulWidget {
  const OptionCLoading({super.key});

  @override
  State<OptionCLoading> createState() => _OptionCLoadingState();
}

class _OptionCLoadingState extends State<OptionCLoading>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 1, milliseconds: 500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF0A0F1A), // 딥 다크 블루 (야간 드론 시점 느낌)
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Viewfinder Animation
            SizedBox(
              width: 150,
              height: 150,
              child: AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return CustomPaint(
                    painter: ViewfinderPainter(_controller.value),
                  );
                },
              ),
            ),
            const SizedBox(height: 40),
            // Text
            FadeTransition(
              opacity: Tween<double>(begin: 0.3, end: 1.0).animate(_controller),
              child: const Column(
                children: [
                  Text(
                    '드론 카메라 시스템 조정 중',
                    style: TextStyle(
                      color: Colors.cyanAccent,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.0,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'CALIBRATING VIDEO FEED',
                    style: TextStyle(
                      color: Colors.white54,
                      fontSize: 10,
                      letterSpacing: 4.0,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ViewfinderPainter extends CustomPainter {
  final double progress; // 0.0 to 1.0

  ViewfinderPainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.cyanAccent
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final double length = 20.0;

    // Animate the size of the brackets: pulse in and out slightly
    final double padding = 20.0 - (progress * 10.0);

    // Top Left
    canvas.drawLine(
      Offset(padding, padding),
      Offset(padding + length, padding),
      paint,
    );
    canvas.drawLine(
      Offset(padding, padding),
      Offset(padding, padding + length),
      paint,
    );

    // Top Right
    canvas.drawLine(
      Offset(size.width - padding, padding),
      Offset(size.width - padding - length, padding),
      paint,
    );
    canvas.drawLine(
      Offset(size.width - padding, padding),
      Offset(size.width - padding, padding + length),
      paint,
    );

    // Bottom Left
    canvas.drawLine(
      Offset(padding, size.height - padding),
      Offset(padding + length, size.height - padding),
      paint,
    );
    canvas.drawLine(
      Offset(padding, size.height - padding),
      Offset(padding, size.height - padding - length),
      paint,
    );

    // Bottom Right
    canvas.drawLine(
      Offset(size.width - padding, size.height - padding),
      Offset(size.width - padding - length, size.height - padding),
      paint,
    );
    canvas.drawLine(
      Offset(size.width - padding, size.height - padding),
      Offset(size.width - padding, size.height - padding - length),
      paint,
    );

    // Center Cross
    final center = Offset(size.width / 2, size.height / 2);
    canvas.drawLine(
      Offset(center.dx - 10, center.dy),
      Offset(center.dx + 10, center.dy),
      paint,
    );
    canvas.drawLine(
      Offset(center.dx, center.dy - 10),
      Offset(center.dx, center.dy + 10),
      paint,
    );

    // Horizontal Scanline moving up and down
    final scanlinePaint = Paint()
      ..color = Colors.cyanAccent.withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    double scanY = padding + (size.height - padding * 2) * progress;
    canvas.drawLine(
      Offset(padding, scanY),
      Offset(size.width - padding, scanY),
      scanlinePaint,
    );
  }

  @override
  bool shouldRepaint(covariant ViewfinderPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

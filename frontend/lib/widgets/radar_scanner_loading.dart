import 'package:flutter/material.dart';

// ==========================================
// 🌟 Option A: AI Radar Scanner Loading UI
// ==========================================
class RadarScannerLoading extends StatefulWidget {
  const RadarScannerLoading({super.key});

  @override
  State<RadarScannerLoading> createState() => _RadarScannerLoadingState();
}

class _RadarScannerLoadingState extends State<RadarScannerLoading>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    // 2초 주기로 반복되는 레이더 회전 애니메이션
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
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
            // Radar Animation Vector
            SizedBox(
              width: 150,
              height: 150,
              child: AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return CustomPaint(
                    painter: RadarPainter(_controller.value),
                    child: const Center(
                      child: Icon(
                        Icons.my_location, // 중앙 타겟 아이콘
                        color: Colors.greenAccent,
                        size: 30,
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 40),
            // Blinking Text (사이버틱한 로딩 문구)
            FadeTransition(
              opacity: Tween<double>(begin: 0.2, end: 1.0).animate(
                CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
              ),
              child: const Column(
                children: [
                  Text(
                    'AI 스트리밍 서버 위치 탐색 중...',
                    style: TextStyle(
                      color: Colors.greenAccent,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.0,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'CONNECTING TO DRONE...',
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

class RadarPainter extends CustomPainter {
  final double sweepProgress; // 0.0 to 1.0

  RadarPainter(this.sweepProgress);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // 1. Draw grid circles
    final gridPaint = Paint()
      ..color = Colors.greenAccent.withOpacity(0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    canvas.drawCircle(center, radius, gridPaint);
    canvas.drawCircle(center, radius * 0.66, gridPaint);
    canvas.drawCircle(center, radius * 0.33, gridPaint);

    // Crosshairs
    canvas.drawLine(
      Offset(center.dx, 0),
      Offset(center.dx, size.height),
      gridPaint,
    );
    canvas.drawLine(
      Offset(0, center.dy),
      Offset(size.width, center.dy),
      gridPaint,
    );

    // 2. Draw sweeping radar cone
    final sweepPaint = Paint()
      ..shader = SweepGradient(
        center: Alignment.center,
        startAngle: 0.0,
        endAngle: 3.14159 * 2, // 360 degrees
        colors: [
          Colors.greenAccent.withOpacity(0.0),
          Colors.greenAccent.withOpacity(0.0),
          Colors.greenAccent.withOpacity(0.5), // Tailing edge of the sweeper
        ],
        stops: [0.0, 0.8, 1.0],
        transform: GradientRotation(sweepProgress * 3.14159 * 2),
      ).createShader(Rect.fromCircle(center: center, radius: radius))
      ..style = PaintingStyle.fill;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      0, // Start
      3.14159 * 2, // End
      true,
      sweepPaint,
    );
  }

  @override
  bool shouldRepaint(covariant RadarPainter oldDelegate) {
    return oldDelegate.sweepProgress != sweepProgress;
  }
}

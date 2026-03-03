import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../services/api_service.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_mjpeg/flutter_mjpeg.dart';
import 'dart:convert';
import '../widgets/option_c_loading.dart';

class LiveStreamingScreenAiOnly extends StatefulWidget {
  final int? missionId;
  const LiveStreamingScreenAiOnly({super.key, this.missionId});

  @override
  State<LiveStreamingScreenAiOnly> createState() =>
      _LiveStreamingScreenAiOnlyState();
}

class _LiveStreamingScreenAiOnlyState extends State<LiveStreamingScreenAiOnly> {
  Position? _currentPosition;
  GoogleMapController? _mapController;

  // WebSocket
  WebSocketChannel? _channel;
  List<dynamic> _detections = [];
  List<dynamic> _windowDetections = []; // Store window bboxes
  int _savedCount = 0;
  bool _showOverlay = true;

  @override
  void initState() {
    super.initState();
    _initLocationService();
    _connectWebSocket();
    print('🎥 [LiveStream MJPEG] Initializing AI-only stream viewer...');
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  void _connectWebSocket() {
    try {
      final wsUrl = ApiService.apiIp.isNotEmpty
          ? 'ws://${ApiService.apiIp}:${ApiService.apiPort}'
          : (dotenv.env['WS_URL'] ?? 'ws://1.238.76.151:8000');

      _channel = WebSocketChannel.connect(Uri.parse('$wsUrl/stream/ws'));

      _channel!.stream.listen(
        (message) {
          try {
            final data = jsonDecode(message);
            if (mounted) {
              setState(() {
                if (data['type'] == 'window') {
                  _windowDetections = data['bboxes'] ?? [];
                } else {
                  // Assuming it's crack or default
                  _detections = [data];
                  if (data.containsKey('saved_count')) {
                    _savedCount = data['saved_count'];
                  }
                }
              });
            }
          } catch (e) {
            print('❌ [WebSocket] Parsing Error: $e');
          }
        },
        onError: (error) {
          print('❌ [WebSocket] Error: $error');
        },
      );
    } catch (e) {
      print('❌ [WebSocket] Connection Failed: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    // Backend MJPEG Stream URL
    final String mjpegStreamUrl = '${ApiService.baseUrl}/stream/live';

    return Scaffold(
      backgroundColor: Colors.black, // Full screen video background
      body: Stack(
        fit: StackFit.expand,
        children: [
          // MJPEG Live Stream (Directly from Backend)
          // 💡 This stream already has the YOLO bounding boxes "burned in" perfectly in sync!
          SizedBox.expand(
            child: FittedBox(
              fit: BoxFit.contain,
              child: _showOverlay
                  ? Mjpeg(
                      isLive: true,
                      stream: mjpegStreamUrl,
                      error: (context, error, stack) =>
                          const OptionCLoading(), // Custom Radar UI
                      loading: (context) =>
                          const OptionCLoading(), // Show while connecting
                    )
                  : const Center(
                      child: Text(
                        'AI 스트림 화면 닫힘',
                        style: TextStyle(color: Colors.white),
                      ),
                    ),
            ),
          ),

          // Custom Bounding Box Painter for Windows
          if (_showOverlay && _windowDetections.isNotEmpty)
            Positioned.fill(
              child: CustomPaint(painter: WindowBBoxPainter(_windowDetections)),
            ),

          // Custom Painter for Crack Re-ID Similarity (Bottom Right)
          if (_showOverlay && _detections.isNotEmpty)
            Positioned.fill(
              child: CustomPaint(painter: CrackSimPainter(_detections)),
            ),

          // Debug Overlay
          Positioned(
            top: 100,
            left: 20,
            child: Container(
              padding: const EdgeInsets.all(8),
              color: Colors.black54,
              child: Text(
                '감지된 균열: $_savedCount',
                style: const TextStyle(
                  color: Colors.yellow,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),

          // Right Controls (Zoom/Filters/Toggle)
          Positioned(
            right: 16,
            top: MediaQuery.of(context).size.height * 0.35,
            child: Column(
              children: [
                // ... (Zoom buttons remain unchanged)
                Container(
                  width: 48,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF101622).withOpacity(0.65),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: _showOverlay ? Colors.green : Colors.white10,
                    ),
                  ),
                  child: Column(
                    children: [
                      IconButton(
                        icon: Icon(
                          _showOverlay ? Icons.layers : Icons.layers_clear,
                          color: _showOverlay ? Colors.green : Colors.grey,
                          size: 20,
                        ),
                        onPressed: () {
                          setState(() {
                            _showOverlay = !_showOverlay;
                          });
                        },
                      ),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text(
                          _showOverlay ? 'AI ON' : 'AI OFF',
                          style: TextStyle(
                            color: _showOverlay ? Colors.green : Colors.grey,
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Bottom Controls (Stop Button & Capture Button)
          Positioned(
            bottom: MediaQuery.of(context).padding.bottom + 24,
            left: 16,
            right: 16,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Stop Button
                Expanded(
                  flex: 5,
                  child: SizedBox(
                    height: 56,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        if (widget.missionId != null) {
                          try {
                            await ApiService.completeMission(widget.missionId!);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('점검이 안전하게 종료되었습니다.'),
                                ),
                              );
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    '종료 중 문제가 발생했습니다. 네트워크 상태를 확인해 주세요.',
                                  ),
                                  backgroundColor: Colors.red,
                                ),
                              );
                            }
                          }
                        }
                        if (context.mounted) {
                          Navigator.pop(context);
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red[600],
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(28),
                        ),
                      ),
                      icon: const Icon(Icons.stop_circle, size: 24),
                      label: const Text(
                        '종료',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Capture Button
                Expanded(
                  flex: 4,
                  child: SizedBox(
                    height: 56,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        HapticFeedback.heavyImpact(); // 햅틱 피드백 '찰칵'
                        if (widget.missionId != null) {
                          try {
                            await ApiService.captureManualSnapshot(
                              widget.missionId!,
                            );
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('선택하신 화면이 안전하게 저장되었습니다.'),
                                  backgroundColor: Colors.green,
                                  duration: Duration(seconds: 2),
                                ),
                              );
                            }
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    '이미지 저장에 실패했습니다. 기기 용량이나 네트워크를 확인해 주세요.',
                                  ),
                                  backgroundColor: Colors.red,
                                ),
                              );
                            }
                          }
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        padding: EdgeInsets.zero,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(28),
                        ),
                      ),
                      icon: const Icon(Icons.camera_alt, size: 24),
                      label: const Text(
                        '캡처',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _initLocationService() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return;
    }

    Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 5,
      ),
    ).listen((Position position) {
      if (mounted) {
        setState(() {
          _currentPosition = position;
        });
      }
    });
  }
}

class WindowBBoxPainter extends CustomPainter {
  final List<dynamic> detections;

  WindowBBoxPainter(this.detections);

  @override
  void paint(Canvas canvas, Size size) {
    if (detections.isEmpty) return;

    final paintOverlay = Paint()
      ..color = Colors.black
          .withOpacity(0.8) // Semi-transparent black for masking
      ..style = PaintingStyle.fill;

    final paintBorder = Paint()
      ..color = Colors.greenAccent
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    for (var detection in detections) {
      if (detection['bbox_norm'] != null) {
        List<dynamic> bboxNorm = detection['bbox_norm'];
        if (bboxNorm.length == 4) {
          // YOLO format: [center_x, center_y, width, height] (normalized)
          double cx = bboxNorm[0] * size.width;
          double cy = bboxNorm[1] * size.height;
          double bw = bboxNorm[2] * size.width;
          double bh = bboxNorm[3] * size.height;

          // Convert to top-left and bottom-right
          double left = cx - (bw / 2);
          double top = cy - (bh / 2);

          final rect = Rect.fromLTWH(left, top, bw, bh);

          // Draw masking overlay
          canvas.drawRect(rect, paintOverlay);
          // Draw border
          canvas.drawRect(rect, paintBorder);

          // Optional: Draw text label (Centered)
          final textPainter = TextPainter(
            text: const TextSpan(
              text: ' 사생활 보호 영역 ',
              style: TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.bold,
                backgroundColor: Colors.black87,
              ),
            ),
            textDirection: TextDirection.ltr,
          );
          textPainter.layout();

          // Draw text exactly in the center of the bounding box
          double textX = cx - (textPainter.width / 2);
          double textY = cy - (textPainter.height / 2);
          textPainter.paint(canvas, Offset(textX, textY));
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant WindowBBoxPainter oldDelegate) {
    return true; // Always repaint when detections change
  }
}

class CrackSimPainter extends CustomPainter {
  final List<dynamic> detections;

  CrackSimPainter(this.detections);

  @override
  void paint(Canvas canvas, Size size) {
    if (detections.isEmpty) return;

    for (var detection in detections) {
      if (detection['bbox'] != null && detection['reid_sim'] != null) {
        List<dynamic> bboxNorm = detection['bbox'];
        if (bboxNorm.length == 4) {
          double cx = bboxNorm[0] * size.width;
          double cy = bboxNorm[1] * size.height;
          double bw = bboxNorm[2] * size.width;
          double bh = bboxNorm[3] * size.height;

          // Bottom right corner of the crack bounding box
          double right = cx + (bw / 2);
          double bottom = cy + (bh / 2);

          double sim = detection['reid_sim'] * 100;
          String matchedText = '';
          if (detection['matched_id'] != null) {
            matchedText = ' (ID: ${detection['matched_id']})';
          }

          final textPainter = TextPainter(
            text: TextSpan(
              text: ' 유사도: ${sim.toStringAsFixed(1)}%$matchedText ',
              style: TextStyle(
                color: sim < 80.0
                    ? Colors.greenAccent
                    : Colors
                          .redAccent, // Green if new crack (<80%), Red if duplicate
                fontSize: 14,
                fontWeight: FontWeight.bold,
                backgroundColor: Colors.black87,
              ),
            ),
            textDirection: TextDirection.ltr,
          );
          textPainter.layout();

          // Draw at bottom right offset
          // Offset slightly so it doesn't overlap exactly with the box lines
          textPainter.paint(canvas, Offset(right + 4, bottom + 4));
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant CrackSimPainter oldDelegate) {
    return true;
  }
}
